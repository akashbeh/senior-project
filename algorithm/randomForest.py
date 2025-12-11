import pandas as pd
from sklearn.ensemble import RandomForestClassifier # Changed from SVM
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import classification_report, accuracy_score
import os
import glob
from datetime import datetime
import numpy as np
import matplotlib.pyplot as plt # For plotting feature importance

# --- Import our existing strategy functions ---
import trading_strategies

print("Starting Random Forest model training script...")

# --- Define Thresholds ---
HOLD_THRESHOLD = 0.02
SUPER_THRESHOLD = 0.1
# --- 1. Load Datasets (Same as SVM) ---
SCRIPT_DIR = os.path.dirname(__file__)
PRICE_FILE = os.path.join(SCRIPT_DIR, 'historical_prices.csv')
SIGNALS_DIR = os.path.join(SCRIPT_DIR, 'daily_signals')

list_of_files = glob.glob(os.path.join(SIGNALS_DIR, '??-??-??_signals.csv'))
if not list_of_files:
    print(f"Error: No signal files found in '{SIGNALS_DIR}'.")
    exit()

def get_date_from_filename(f):
    basename = os.path.basename(f)
    date_str = basename.split('_signals.csv')[0]
    return datetime.strptime(date_str, '%y-%m-%d')

latest_file = max(list_of_files, key=get_date_from_filename)
print(f"Loading latest signals file: {latest_file}")

try:
    prices_df = pd.read_csv(PRICE_FILE, parse_dates=['date'])
    sentiment_df = pd.read_csv(latest_file, parse_dates=['timestamp'])
except FileNotFoundError as e:
    print(f"Error loading files: {e}")
    exit()

if 'Ticker' in prices_df.columns:
    prices_df.rename(columns={'Ticker': 'ticker'}, inplace=True)

# --- 2. Feature Engineering (Same as SVM) ---
print("Engineering features...")
prices_df.sort_values(by=['ticker', 'date'], inplace=True)
periods = {
    'change_day': 1, 'change_week': 5, 'change_month': 21,
    'change_3mo': 63, 'change_6mo': 126, 'change_9mo': 189, 'change_1yr': 252
}
for name, period in periods.items():
    prices_df[name] = prices_df.groupby('ticker')['Adj Close'].pct_change(periods=period, fill_method=None)

prices_df['next_day_pct_change'] = prices_df.groupby('ticker')['Adj Close'].pct_change(periods=-1, fill_method=None).shift(1)

def create_target(pct_change):
    if pct_change > SUPER_THRESHOLD: return 2
    elif pct_change > HOLD_THRESHOLD: return 1
    elif pct_change > -SUPER_THRESHOLD and pct_change < -HOLD_THRESHOLD: return -1 
    elif pct_change < -SUPER_THRESHOLD: return -2
    else: return 0

prices_df['target'] = prices_df['next_day_pct_change'].apply(create_target)

sentiment_df.rename(columns={'timestamp': 'date'}, inplace=True)
prices_df['ticker'] = prices_df['ticker'].astype(str)
sentiment_df['ticker'] = sentiment_df['ticker'].astype(str)
data = pd.merge(prices_df, sentiment_df, on=['ticker', 'date'], how='inner')
data.dropna(inplace=True)

if data.empty:
    print("Error: No data available for training.")
    exit()

feature_cols = [
    'change_day', 'change_week', 'change_month', 'change_3mo',
    'change_6mo', 'change_9mo', 'change_1yr',
    'mean_sentiment', 'comment_count', 'sentiment_change', 'volume_change', 'svc'
]
X = data[feature_cols]
y = data['target']

split_index = int(len(X) * 0.8)
X_train, y_train = X.iloc[:split_index], y.iloc[:split_index]
X_test, y_test = X.iloc[split_index:], y.iloc[split_index:]

# Random Forest doesn't strictly need scaling, but it helps convergence and consistency
scaler = StandardScaler()
X_train_scaled = scaler.fit_transform(X_train)
X_test_scaled = scaler.transform(X_test)

# --- 3. Train Random Forest Model ---
print("Training Random Forest Classifier...")
# n_estimators=100 means it builds 100 different decision trees
model = RandomForestClassifier(n_estimators=500, random_state=42)
model.fit(X_train_scaled, y_train)
print("Model training complete.")

# --- 4. Evaluate Model ---
y_pred = model.predict(X_test_scaled)
y_probs = model.predict_proba(X_test_scaled)

print(y_probs)
print("\n" + "="*30)
print("   Random Forest Evaluation")
print("="*30)
print(f"Accuracy: {accuracy_score(y_test, y_pred) * 100:.2f}%")
print("\nClassification Report:")
print(classification_report(y_test, y_pred, target_names=['Super Sell(-2)', 'Sell (-1)', 'Hold (0)', 'Buy (1)', 'Super Buy(2)'], zero_division=0))

# --- 5. Feature Importance (Specific to Random Forest) ---
print("\n--- Feature Importance ---")
importances = model.feature_importances_
indices = np.argsort(importances)[::-1]

print("Which features mattered most?")
for i in range(len(feature_cols)):
    print(f"{i+1}. {feature_cols[indices[i]]}: {importances[indices[i]]:.4f}")

# --- 6. Backtest Simulation ---
print("\n" + "="*30)
print("   Backtesting Simulation")
print("="*30)

test_data = data.iloc[split_index:].copy()
test_data['signal'] = y_pred

# Run strategies using your existing module
rf_results = trading_strategies.run_svm_strategy(test_data) # We reuse the function logic, just passing RF predictions
# Rename the strategy column for clarity
rf_results['strategy'] = 'Random Forest'

bnh_results = trading_strategies.run_buy_and_hold_strategy(test_data)
svc_results = trading_strategies.run_raw_svc_strategy(test_data)

all_results = pd.concat([rf_results, bnh_results, svc_results])

print("\n--- Average (Portfolio) Results ---")
avg_results = all_results.groupby('strategy').mean(numeric_only=True)
avg_results = avg_results.reindex(['Random Forest', 'Raw SVC Signal', 'Buy and Hold'])

# Format for display
avg_results['final_value'] = avg_results['final_value'].map('${:,.2f}'.format)
avg_results['profit'] = avg_results['profit'].map('${:,.2f}'.format)
avg_results['total_return_pct'] = avg_results['total_return_pct'].map('{:.2%}'.format)
avg_results['risk_pct'] = avg_results['risk_pct'].map('{:.2%}'.format)
avg_results['sharpe_ratio'] = avg_results['sharpe_ratio'].map('{:.2f}'.format)

print(avg_results.to_string())
print("="*30)