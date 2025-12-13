import pandas as pd
import numpy as np
import os
import glob
from datetime import date

# --- Define input and output directories ---
# This script is in 'sentiment_algo', so we go up one level
SCRIPT_DIR = os.path.dirname(__file__)
PROJECT_ROOT = os.path.join(SCRIPT_DIR, "..")

INPUT_DIR = os.path.join(PROJECT_ROOT, 'sentiment_algo', "daily_sentiment")
OUTPUT_DIR = os.path.join(PROJECT_ROOT, 'sentiment_algo', "daily_signals")
os.makedirs(OUTPUT_DIR, exist_ok=True)

# --- Load and Combine All Daily Sentiment Files ---
# NEW: Look for 'YY-MM-DD.csv' files. This pattern will find '25-10-13.csv' etc.
file_pattern = os.path.join(INPUT_DIR, "??-??-??.csv") 
all_files = glob.glob(file_pattern)

if not all_files:
    print(f"Error: No daily sentiment files found in '{INPUT_DIR}' matching pattern 'YY-MM-DD.csv'.")
    exit()

print(f"Found {len(all_files)} combined daily sentiment files. Combining them...")

df_list = [pd.read_csv(file) for file in all_files]
df = pd.concat(df_list, ignore_index=True)
df['timestamp'] = pd.to_datetime(df['timestamp'], errors='coerce') # errors='coerce' ensures bad dates become NaT

# --- FIX IS HERE ---
original_count = len(df)
df.dropna(subset=['timestamp'], inplace=True) # Drop any rows where the timestamp is NaT
new_count = len(df)
if original_count > new_count:
    print(f"INFO: Dropped {original_count - new_count} rows with invalid/missing timestamps.")
# --- END FIX ---

print(f"Successfully combined all data. Total valid entries: {len(df)}")

# --- Daily Aggregation ---
df.set_index('timestamp', inplace=True)
df.sort_index(inplace=True) # Sort by date to ensure correct .diff()

daily_stats = df.groupby('ticker').resample('D').agg(
    mean_sentiment=('sentiment_score', 'mean'),
    comment_count=('ticker', 'count') 
).fillna(0)

# --- SVC Calculation ---
def calculate_svc(group):
    group['sentiment_change'] = group['mean_sentiment'].diff()
    group['volume_change'] = group['comment_count'].diff().abs()
    group['svc'] = group['sentiment_change'] * group['volume_change']
    return group

print("Calculating overall SVC metric for each stock...")
df_svc = daily_stats.groupby(level=0, group_keys=False).apply(calculate_svc)
df_svc.replace([np.inf, -np.inf], np.nan, inplace=True)
df_svc.fillna(0, inplace=True)

print("📈 Overall SVC Calculation Complete.")

# --- Save Master Signal File ---
today_str = date.today().strftime('%y-%m-%d')
output_path = os.path.join(OUTPUT_DIR, f"{today_str}_signals.csv")
df_svc.to_csv(output_path)
print(f"\n💾 Complete historical SVC signal data saved to: {output_path}")