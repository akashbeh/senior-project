import pandas as pd
from sklearn.svm import SVC
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import classification_report, accuracy_score
import os
import numpy as np
import trading_strategies

print("Starting SVM multiclass model training script...")

INPUT_FILE = "merged_data.csv"

SCRIPT_DIR = os.path.dirname(__file__)
ROOT_DIR = os.path.join(SCRIPT_DIR, "..")
INPUT = os.path.join(ROOT_DIR, INPUT_FILE)

data = None
try:
    data = pd.read_csv(INPUT, parse_dates=['date'])
    print(f"Successfully loaded {INPUT}")
except FileNotFoundError:
    print(f"Error: '{INPUT}' not found. Please run download_price_history.py first.")
    exit()

HOLD_THRESHOLD = 0.02  # Any move between -2% and +2% is a "Hold"
SUPER_THRESHOLD = 0.1

data.dropna(inplace=True)

if data.empty:
    print("Error: No data remaining after merging and cleaning. Check your data files.")
    exit()

print(f"Total {len(data)} data points ready for training.")

feature_cols = [
    'change_day', 'change_week', 'change_month', 'change_3mo',
    'change_6mo', 'change_9mo', 'change_1yr',
    'mean_sentiment', 'comment_count', 'sentiment_change', 'volume_change', 'svc'
]

X = data[feature_cols]
y = data['target']

print("\nClass Distribution in dataset:")
print(y.value_counts(normalize=True) * 100)

split_index = int(len(X) * 0.8)
X_train, y_train = X.iloc[:split_index], y.iloc[:split_index]
X_test, y_test = X.iloc[split_index:], y.iloc[split_index:]

print(f"\nTraining on {len(X_train)} samples, testing on {len(X_test)} samples.")

if X_train.empty or X_test.empty:
     print("Error: Not enough data for train/test split.")
     exit()

scaler = StandardScaler()
X_train_scaled = scaler.fit_transform(X_train)
X_test_scaled = scaler.transform(X_test)

print("Training SVM model with RBF kernel...")
model = SVC(kernel='rbf', C=1.0, gamma='auto')
model.fit(X_train_scaled, y_train)
print("Model training complete.")


y_pred = model.predict(X_test_scaled)
print("\n" + "="*30)
print("   Model Evaluation Results")
print("="*30)
print(f"Accuracy: {accuracy_score(y_test, y_pred) * 100:.2f}%")
print("\nClassification Report:")
print(classification_report(
    y_test, 
    y_pred, 
    target_names=['Super Sell(-2)', 'Sell (-1)', 'Hold (0)', 'Buy (1)', 'Super Buy(2)'],
    zero_division=0
))
print("="*30)
print("\n" + "="*60)
print("-----------BACKTESTING WITH 100 AGAINST B&H--------------")
print("="*60)

# 1. Prepare test data for the strategy functions
test_data = data.iloc[split_index:].copy()
test_data['signal'] = y_pred # Add the model's predictions

# 2. Run all strategies
svm_results = trading_strategies.run_svm_strategy(test_data)
bnh_results = trading_strategies.run_buy_and_hold_strategy(test_data)
svc_results = trading_strategies.run_raw_svc_strategy(test_data) # Bonus strategy

# 3. Combine and display results
all_results = pd.concat([svm_results, bnh_results, svc_results])

# --- Show Ticker-by-Ticker Results ---
print("\n--- Detailed Results per Ticker (Top 10 by SVM Profit) ---")
ticker_pivot = all_results.pivot(index='ticker', columns='strategy', values='profit')
# Reorder columns for logical comparison
ticker_pivot = ticker_pivot[['SVM Model', 'Raw SVC Signal', 'Buy and Hold']]
print(ticker_pivot.sort_values(by='SVM Model', ascending=False).head(10).to_string(float_format="%.2f"))

# --- Show Average (Portfolio) Results ---
print("\n--- Average (Portfolio) Results Across All Tickers ---")
avg_results = all_results.groupby('strategy').mean(numeric_only=True)
# Reorder index for logical comparison
avg_results = avg_results.reindex(['SVM Model', 'Raw SVC Signal', 'Buy and Hold'])
# Format for display
avg_results['final_value'] = avg_results['final_value'].map('${:,.2f}'.format)
avg_results['profit'] = avg_results['profit'].map('${:,.2f}'.format)
avg_results['total_return_pct'] = avg_results['total_return_pct'].map('{:.2%}'.format)
avg_results['risk_pct'] = avg_results['risk_pct'].map('{:.2%}'.format)
avg_results['sharpe_ratio'] = avg_results['sharpe_ratio'].map('{:.2f}'.format)

print(avg_results.to_string())
print("="*30) 
all_results = pd.concat([svm_results, bnh_results, svc_results])
print(all_results)
print('='*30)
