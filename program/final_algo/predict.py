import os
import joblib
import pandas as pd
import trading_strategies

DATA_FILE = "present_data.csv"

SCRIPT_DIR = os.path.dirname(__file__)
ROOT_DIR = os.path.join(SCRIPT_DIR, "..")
DATA_DIR = os.path.join(ROOT_DIR, "data")

DATA = os.path.join(DATA_DIR, DATA_FILE)

# Load data
data = None
try:
    data = pd.read_csv(DATA, parse_dates=['date'])
    print(f"Successfully loaded {DATA}")
except FileNotFoundError:
    print(f"Error: '{DATA}' not found.")
    exit()

feature_cols = [
    'change_day', 'change_week', 'change_month', 'change_3mo',
    'change_6mo', 'change_9mo', 'change_1yr',
    'mean_sentiment', 'comment_count', 'sentiment_change', 'volume_change', 'svc',
    'Buyer Change Day', 'Buyer Change Week', 'Buyer Change Month', 'Buyer Change TriMonth',
    'Trade Direction Day', 'Trade Direction Week', 'Trade Direction Month', 'Trade Direction TriMonth'
]

# Load model
MODEL_DIR = "rf_full"

scaler = joblib.load(f"{MODEL_DIR}/scaler.joblib")
model = joblib.load(f"{MODEL_DIR}/rf_model.joblib")

X = data[feature_cols]
X_scaled = scaler.transform(X)

data["signal"] = model.predict(X_scaled)

THRESHOLDS = [
    ("Small", 0.025),
    ("Mid", 0.05),
    ("Great", 0.1),
    ("Huge", 0.2),
    ("Tremendous", 0.4),
    ("Absurd", 0.8),
]

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
    res = strategy.run(model, feature_cols, scaler, data, printing=True)
    results.append(res)
