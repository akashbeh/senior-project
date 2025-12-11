import pandas as pd
from sklearn.svm import SVC
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import classification_report, accuracy_score
import os
import glob
from datetime import datetime
import numpy as np
import trading_strategies

print("Starting SVM multiclass model training script...")


HOLD_THRESHOLD = 0.02  # Any move between -2% and +2% is a "Hold"
SUPER_THRESHOLD = 0.1
SCRIPT_DIR = os.path.dirname(__file__)
PRICE_FILE = os.path.join(SCRIPT_DIR, 'historical_prices.csv')
SIGNALS_DIR = os.path.join(SCRIPT_DIR, 'daily_signals')

list_of_files = glob.glob(os.path.join(SIGNALS_DIR, '??-??-??_signals.csv')) # Use YY-MM-DD format
if not list_of_files:
    print(f"Error: No signal files found in '{SIGNALS_DIR}' matching 'YY-MM-DD_signals.csv'.")
    exit()

def get_date_from_filename(f):
    basename = os.path.basename(f)
    date_str = basename.split('_signals.csv')[0]
    return datetime.strptime(date_str, '%y-%m-%d') # Use %y-%m-%d format

latest_file = max(list_of_files, key=get_date_from_filename)
print(f"Loading latest signals file: {latest_file}")

try:
    prices_df = pd.read_csv(PRICE_FILE, parse_dates=['date'])
    print(f"Successfully loaded {PRICE_FILE}")
except FileNotFoundError:
    print(f"Error: '{PRICE_FILE}' not found. Please run download_price_history.py first.")
    exit()

try:
    sentiment_df = pd.read_csv(latest_file, parse_dates=['timestamp'])
    print(f"Successfully loaded {latest_file}")
except FileNotFoundError:
    print(f"Error: '{latest_file}' not found. Please run your pipeline first.")
    exit()

if 'Ticker' in prices_df.columns:
    prices_df.rename(columns={'Ticker': 'ticker'}, inplace=True)


print("Engineering price features...")
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
print("Merging sentiment and price data...")
sentiment_df.rename(columns={'timestamp': 'date'}, inplace=True)

prices_df['ticker'] = prices_df['ticker'].astype(str)
sentiment_df['ticker'] = sentiment_df['ticker'].astype(str)

data = pd.merge(
    prices_df, 
    sentiment_df, 
    on=['ticker', 'date'], 
    how='inner'
)

agent_data_path = os.path.join(SCRIPT_DIR, 'full_merged_data.csv')
data.to_csv(agent_data_path, index=False)
print(f"✅ Agent data file saved to: {agent_data_path}")

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
