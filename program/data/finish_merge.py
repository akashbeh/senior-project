import pandas as pd
from sklearn.svm import SVC
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import classification_report, accuracy_score
import os
from datetime import datetime
import numpy as np

PRICES_AND_SENTIMENT = "merged_data.csv"
INSIDER = "2020-clean.csv"
OUTPUT = "full_full_data.csv"

SCRIPT_DIR = os.path.dirname(__file__)
ROOT_DIR = os.path.join(SCRIPT_DIR, "..")
DATA_DIR = os.path.join(ROOT_DIR, "data")

SEMI_FULL = os.path.join(DATA_DIR, PRICES_AND_SENTIMENT)
INSIDER = os.path.join(DATA_DIR, 'insider-data', INSIDER)
OUTPUT_DATA = os.path.join(DATA_DIR, OUTPUT)

print("Starting Random Forest multiclass model training script...")

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

