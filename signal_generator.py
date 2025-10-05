import pandas as pd
import numpy as np
import os
import glob

# --- Define input and output directories ---
input_dir = "daily_sentiment"
output_dir = "daily_signals"
os.makedirs(output_dir, exist_ok=True)

# --- Load and Combine All Daily Sentiment Files ---
# DEBUG PRINT: Show what pattern we are looking for
print(f"DEBUG: Searching for files matching pattern: {os.path.join(input_dir, '*.csv')}")

all_files = glob.glob(os.path.join(input_dir, "*.csv"))

# DEBUG PRINT: Show all the files that were found
if not all_files:
    print(f"Error: No daily sentiment files found in the '{input_dir}' directory.")
    exit()
else:
    print(f"\nDEBUG: Found {len(all_files)} files to load:")
    for f in all_files:
        print(f"  - {f}")

# Change the list comprehension to a loop to add a print statement
df_list = []
for file in all_files:
    # DEBUG PRINT: Show each file as it's being read
    print(f"DEBUG: Reading file: {file}")
    df_list.append(pd.read_csv(file))

df = pd.concat(df_list, ignore_index=True)
df['timestamp'] = pd.to_datetime(df['timestamp'])

# DEBUG PRINT: Show the size of the combined DataFrame
print(f"\nDEBUG: Combined DataFrame has {df.shape[0]} rows and {df.shape[1]} columns.")


# --- Daily Aggregation ---
df.set_index('timestamp', inplace=True)
df.sort_index(inplace=True)

# DEBUG PRINT: Show the date range of the combined data
print(f"DEBUG: Data sorted. Date range is from {df.index.min()} to {df.index.max()}.")


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

print("\nCalculating the SVC metric...")
df_svc = daily_stats.groupby(level=0, group_keys=False).apply(calculate_svc)
df_svc.replace([np.inf, -np.inf], np.nan, inplace=True)
df_svc.fillna(0, inplace=True)

print("📈 SVC Calculation Complete.")

# --- Save to a new daily file in the output directory ---
from datetime import date
today_str = date.today().strftime('%y-%m-%d')
output_filename = f"{today_str}_signals.csv"
output_path = os.path.join(output_dir, output_filename)

df_svc.to_csv(output_path)
print(f"\n💾 Complete historical SVC signal data saved to: {output_path}")

# DEBUG PRINT: Show the final output for a specific ticker to verify calculations
print("\n--- DEBUG: Final calculated data for TSLA (last 5 rows) ---")
try:
    print(df_svc[df_svc.index.get_level_values('ticker') == 'TSLA'].tail())
except:
    print("Could not find data for TSLA to display.")