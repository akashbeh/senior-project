import pandas as pd
from sklearn.svm import SVC
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import classification_report, accuracy_score
import os
from datetime import datetime
import numpy as np
import trading_strategies

INPUT_FILE = "full_full_data.csv"

SCRIPT_DIR = os.path.dirname(__file__)
ROOT_DIR = os.path.join(SCRIPT_DIR, "..")
DATA_DIR = os.path.join(ROOT_DIR, "data")

FULL = os.path.join(DATA_DIR, INPUT_FILE)

THRESHOLDS = [
    ("Small", 0.025),
    ("Mid", 0.05),
    ("Great", 0.1),
    ("Huge", 0.2),
    ("Tremendous", 0.4),
    ("Absurd", 0.8),
]

data = None
try:
    data = pd.read_csv(FULL, parse_dates=['date'])
    print(f"Successfully loaded {FULL}")
except FileNotFoundError:
    print(f"Error: '{FULL}' not found.")
    exit()

# SVM TRAINING
print(f"Total {len(data)} data points ready for training and testing.")

feature_cols = [
    'change_day', 'change_week', 'change_month', 'change_3mo',
    'change_6mo', 'change_9mo', 'change_1yr',
    'mean_sentiment', 'comment_count', 'sentiment_change', 'volume_change', 'svc',
    'Buyer Change Day', 'Buyer Change Week', 'Buyer Change Month', 'Buyer Change TriMonth',
    'Trade Direction Day', 'Trade Direction Week', 'Trade Direction Month', 'Trade Direction TriMonth'
]

X = data[feature_cols]
y = data['target']

print("\nClass Distribution in dataset:")
print(y.value_counts(normalize=True) * 100)

all_classes = sorted(y.unique())

# Test-training split
data["date"] = pd.to_datetime(data["date"],errors="coerce")
#data.dropna(subset=["date"],inplace=True)

data = data.sort_values(["date"])
data = data.reset_index(drop=True)
# Start in March 2020 so that the 3-month rolling sum is accurate
start_index = data.index[data["date"] >= pd.Timestamp("2020-03-01")][0]
end_index = data.index[data["date"] < pd.Timestamp("2021-01-01")][-1]
split_index = int((end_index - start_index) * 0.8 + start_index)

test_data = data.iloc[split_index:end_index].copy()

X_train = X.iloc[start_index:split_index]
y_train = y.iloc[start_index:split_index]
X_test = X.iloc[split_index:end_index]
y_test = y.iloc[split_index:end_index]

print(f"\nTraining on {len(X_train)} samples, testing on {len(X_test)} samples.")

if X_train.empty or X_test.empty:
     print("Error: Not enough data for train/test split.")
     exit()

scaler = StandardScaler()
X_train_scaled = scaler.fit_transform(X_train)
X_test_scaled = scaler.transform(X_test)

#print("Training SVM model with RBF kernel...")
#model = SVC(kernel='rbf', C=1.0, gamma='auto')
print("Training Random Forest Classifier...")
model = RandomForestClassifier(n_estimators=500, random_state=42)
model.fit(X_train_scaled, y_train)
print("Model training complete.")


y_pred = model.predict(X_test_scaled)
#y_probs = model.predict_proba(X_test_scaled)
print("\n" + "="*30)
print("   Model Evaluation Results")
print("="*30)
print(f"Accuracy: {accuracy_score(y_test, y_pred) * 100:.2f}%")
print("\nClassification Report:")

target_names = list()
for classs in all_classes:
    name = None
    if classs == 0:
        name = "Hold (0)"
    else:
        threshold_name, _ = THRESHOLDS[int(abs(classs) - 1)]
        if classs > 0:
            name = f"{threshold_name} Buy ({classs})"
        else:
            name = f"{threshold_name} Sell ({classs})"
    target_names.append(name)

print(classification_report(
    y_test, 
    y_pred, 
    labels=all_classes,
    target_names=target_names,
    zero_division=0
))

# --- Feature Importance (Specific to Random Forest) ---
print("\n--- Feature Importance ---")
importances = model.feature_importances_
indices = np.argsort(importances)[::-1]

print("Which features mattered most?")
for i in range(len(feature_cols)):
    print(f"{i+1}. {feature_cols[indices[i]]}: {importances[indices[i]]:.4f}")



print("="*30)
print("\n" + "="*60)
print("-----------BACKTESTING WITH 100 AGAINST B&H--------------")
print("="*60)

# 1. Prepare test data for the strategy functions
test_data['signal'] = y_pred # Add the model's predictions

# 2. Run all strategies
results = list()

STRATEGIES = [
    trading_strategies.Svm(), 
    trading_strategies.BuyAndHold(), 
    trading_strategies.RawSvc(), 
    trading_strategies.SoftMax(beta=0.5, thresholds=THRESHOLDS), 
    trading_strategies.SoftMax(beta=1.0, thresholds=THRESHOLDS), 
    trading_strategies.SoftMax(beta=2.0, thresholds=THRESHOLDS)
]
for strategy in STRATEGIES:
    res = strategy.run(model, feature_cols, scaler, test_data)
    results.append(res)

# 3. Combine and display results
all_results = pd.concat(results, ignore_index=True)
print(all_results)
