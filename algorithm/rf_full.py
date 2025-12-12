import pandas as pd
from sklearn.svm import SVC
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import classification_report, accuracy_score
import os
import glob
from datetime import datetime
import numpy as np
import trading_strategies

print("Starting SVM multiclass model training script...")

THRESHOLDS = [
    ("Small", 0.025),
    ("Mid", 0.05),
    ("Great", 0.1),
    ("Huge", 0.2),
    ("Tremendous", 0.4),
    ("Absurd", 0.8),
]

SCRIPT_DIR = os.path.dirname(__file__)
SEMI_FULL = os.path.join(SCRIPT_DIR, 'full_merged_data.csv')
INSIDER = os.path.join(SCRIPT_DIR, 'insider-data/2020-clean.csv')
OUTPUT_DATA = os.path.join(SCRIPT_DIR, 'full_full_data.csv')

# Load dataframes
try:
    semifull_df = pd.read_csv(SEMI_FULL, parse_dates=['date'])
    print(f"Successfully loaded {SEMI_FULL}")
except FileNotFoundError:
    print(f"Error: '{SEMI_FULL}' not found.")
    exit()

try:
    insider_df = pd.read_csv(INSIDER, parse_dates=['Date'])
    print(f"Successfully loaded {INSIDER}")
except FileNotFoundError:
    print(f"Error: '{INSIDER}' not found.")
    exit()


insider_df.sort_values(by=['Ticker', 'Date'], inplace=True)

# Engineering target
def create_target(pct_change):
    thresholds_passed = 0
    for (_, threshold) in THRESHOLDS:
        if abs(pct_change) > threshold:
            thresholds_passed += 1
    
    if pct_change < 0:
        return - thresholds_passed
    else:
        return thresholds_passed

semifull_df['target'] = semifull_df['next_day_pct_change'].apply(create_target)

insider_df.rename(columns={'Ticker': 'ticker'}, inplace=True)
insider_df.rename(columns={'Date': 'date'}, inplace=True)

# Ensure type compatibility
for df in [insider_df, semifull_df]:
    df["ticker"] = df["ticker"].astype(str)
    df["date"] = pd.to_datetime(df["date"], format="mixed")

# Merge
data = pd.merge(
    insider_df, 
    semifull_df, 
    on=['ticker', 'date'], 
    how='left',
    suffixes=("", "_trade")
)


# Fill rows with no insider data
data = data.sort_values(["ticker", "date"])
cols_to_fill = [
    'Buyer Change Day', 'Buyer Change Week', 'Buyer Change Month', 'Buyer Change TriMonth',
    'Trade Direction Day', 'Trade Direction Week', 'Trade Direction Month', 'Trade Direction TriMonth'
]
data[cols_to_fill] = data.groupby("ticker")[cols_to_fill].ffill()

# Sort
data = data.sort_values(["ticker", "date"])
# Drop empty rows
data.dropna(inplace=True)
if data.empty:
    print("Error: No data remaining after merging and cleaning.")
    exit()

# Save
data.to_csv(OUTPUT_DATA, index=False)
print(f"✅ Agent data file saved to: {OUTPUT_DATA}")



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
# Start in March 2020 so that we have 3 months of earlier data
start_index = data.index[data["date"] >= pd.Timestamp("2020-03-01")][0]
print("Start")
print(start_index)
end_index = data.index[data["date"] < pd.Timestamp("2021-01-01")][-1]
print("End")
print(end_index)
split_index = int((end_index - start_index) * 0.8 + start_index)
print("Split")
print(split_index)

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

'''
target_names = list()
for i, (name, _) in enumerate(THRESHOLDS):
    j = i + 1
    target_names.append(f"{name} Buy ({j})")
target_names.insert(0, "Hold (0)")
for i, (name, _) in enumerate(THRESHOLDS):
    j = i + 1
    target_names.insert(0, f"{name} Sell (-{j})")
'''
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
