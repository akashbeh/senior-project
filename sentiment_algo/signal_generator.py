import pandas as pd
import numpy as np
import os
import glob
from datetime import date, timedelta

# --- Configuration ---
input_dir = "daily_sentiment"
output_dir = "daily_signals"
os.makedirs(output_dir, exist_ok=True)

# --- Load and Combine All Daily Sentiment Files ---
all_files = glob.glob(os.path.join(input_dir, "*.csv"))
if not all_files:
    print(f"Error: No daily sentiment files found in the '{input_dir}' directory.")
    exit()

df_list = [pd.read_csv(file) for file in all_files]
df = pd.concat(df_list, ignore_index=True)
df['timestamp'] = pd.to_datetime(df['timestamp'])
df.set_index('timestamp', inplace=True)
df.sort_index(inplace=True)

# --- NEW: Check for data continuity ---
most_recent_date = df.index.max().date()
yesterday = most_recent_date - timedelta(days=1)
# Check if there is any data from yesterday in the index
if yesterday not in df.index.date: #type: ignore
    print(f"⚠️ WARNING: Data for the previous day ({yesterday}) is missing. Change calculations may be inaccurate or zero.")

# --- Daily Aggregation ---
daily_stats = df.groupby('ticker').resample('D').agg(
    mean_sentiment=('sentiment_score', 'mean'),
    comment_count=('comment_id', 'count')
).fillna(0)

# --- SVC Calculation ---
def calculate_svc(group):
    group['sentiment_change'] = group['mean_sentiment'].diff()
    group['volume_change'] = group['comment_count'].diff().abs()
    group['svc'] = group['sentiment_change'] * group['volume_change']
    return group

print("Calculating the SVC metric...")
df_svc = daily_stats.groupby(level=0, group_keys=False).apply(calculate_svc)
df_svc.replace([np.inf, -np.inf], np.nan, inplace=True)
df_svc.fillna(0, inplace=True)

# --- Save to a new daily file ---
today_str = date.today().strftime('%y-%m-%d')
output_filename = f"{today_str}_signals.csv"
output_path = os.path.join(output_dir, output_filename)
df_svc.to_csv(output_path)
print(f"💾 Complete historical SVC signal data saved to: {output_path}")