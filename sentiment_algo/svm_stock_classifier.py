import pandas as pd
from sklearn.svm import SVC
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import classification_report, accuracy_score
from sklearn.model_selection import train_test_split, GridSearchCV, learning_curve
import os
import numpy as np
from datetime import date


print("Starting SVM multiclass model training script...")

# --- Define Thresholds ---
# We need to define what counts as a "Buy", "Sell", or "Hold".
# These are percentages (e.g., 0.02 = 2%). You can tune these.
HOLD_THRESHOLD = 0.02  # Any move between -2% and +2% is a "Hold"
# Any move > +2% is a "Buy"
# Any move < -2% is a "Sell"

# --- 1. Load Datasets ---
today_str = date.today().strftime('%y-%m-%d')
SCRIPT_DIR = os.path.dirname(__file__)
PRICE_FILE = os.path.join(SCRIPT_DIR, 'historical_prices.csv')
SENTIMENT_FILE = os.path.join(SCRIPT_DIR, '..', 'sentiment_algo', 'daily_signals', f'{today_str}_signals.csv')

try:
    prices_df = pd.read_csv(PRICE_FILE, parse_dates=['date'])
    print(f"Successfully loaded {PRICE_FILE}")
except FileNotFoundError:
    print(f"Error: '{PRICE_FILE}' not found. Please run download_price_history.py first.")
    exit()

try:
    sentiment_df = pd.read_csv(SENTIMENT_FILE, parse_dates=['timestamp'])
    print(f"Successfully loaded {SENTIMENT_FILE}")
except FileNotFoundError:
    print(f"Error: '{SENTIMENT_FILE}' not found. Please run your pipeline first.")
    exit()

# --- 2. Feature Engineering (Historical Prices) ---
print("Engineering price features...")
prices_df.sort_values(by=['ticker', 'date'], inplace=True)

periods = {
    'change_day': 1, 'change_week': 5, 'change_month': 21,
    'change_3mo': 63, 'change_6mo': 126, 'change_9mo': 189, 'change_1yr': 252
}

for name, period in periods.items():
    prices_df[name] = prices_df.groupby('ticker')['Adj Close'].pct_change(periods=period)

# --- 3. Feature Engineering (NEW Target Variable 'y') ---
# Calculate the *percentage change* for the next day.
prices_df['next_day_pct_change'] = prices_df.groupby('ticker')['Adj Close'].pct_change(periods=-1).shift(1)

# Define the 3-class target variable
def create_target(pct_change):
    if pct_change > HOLD_THRESHOLD:
        return 1  # Buy
    elif pct_change < -HOLD_THRESHOLD:
        return -1 # Sell
    else:
        return 0  # Hold

prices_df['target'] = prices_df['next_day_pct_change'].apply(create_target)

# --- 4. Combine Data ---
print("Merging sentiment and price data...")
sentiment_df.rename(columns={'timestamp': 'date'}, inplace=True)

data = pd.concat(
    prices_df, 
    sentiment_df, 
    on=['ticker', 'date'], 
    how='inner'
)

# --- 5. Build and Train Model ---
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

# Check class distribution
print("\nClass Distribution in dataset:")
print(y.value_counts(normalize=True) * 100)

# Time-Series Train/Test Split (80% train, 20% test)
split_index = int(len(X) * 0.8)

X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

print(f"\nTraining on {len(X_train)} samples, testing on {len(X_test)} samples.")

if X_train.empty or X_test.empty:
     print("Error: Not enough data for train/test split.")
     exit()

# Scale the features
scaler = StandardScaler()
X_train_scaled = scaler.fit_transform(X_train)
X_test_scaled = scaler.transform(X_test)

# Initialize SVM for multiclass classification
print("Training SVM model with RBF kernel...")
# SVC automatically handles multiclass classification using a "one-vs-one" strategy
model = SVC(kernel='rbf', C=1.0, gamma='auto')

# Fit the model
model.fit(X_train_scaled, y_train)
print("Model training complete.")

# --- 6. Evaluate Model ---
y_pred = model.predict(X_test_scaled)

print("\n" + "="*30)
print("   Model Evaluation Results")
print("="*30)
print(f"Accuracy: {accuracy_score(y_test, y_pred) * 100:.2f}%")
print("\nClassification Report:")
# NEW: Updated target_names for the 3 classes
print(classification_report(
    y_test, 
    y_pred, 
    target_names=['Sell (-1)', 'Hold (0)', 'Buy (1)'],
    zero_division_zero=True
))
print("="*30)