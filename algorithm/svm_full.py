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
    if pct_change > SUPER_THRESHOLD: return 2
    elif pct_change > HOLD_THRESHOLD: return 1
    elif pct_change > -SUPER_THRESHOLD and pct_change < -HOLD_THRESHOLD: return -1 
    elif pct_change < -SUPER_THRESHOLD: return -2
    else: return 0

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

# Start in March 2020 so that we have 3 months of earlier data
data["date"] = pd.to_datetime(data["date"])
start_index = data.index[data["date"] >= pd.Timestamp("2020-03-01")][0]
split_index = int((len(X) - start_index) * 0.8)
X_train, y_train = X.iloc[start_index:split_index], y.iloc[start_index:split_index]
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
results = list()
for strategy in trading_strategies.STRATEGIES:
    res = strategy.run(test_data)
    results.append(res)

# 3. Combine and display results
all_results = pd.concat(results)

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
all_results = pd.concat(results)
print(all_results)
print('='*30)
