import os
import glob
import pandas as pd
from datetime import datetime

PRICES_FILE = 'historical_prices.csv'
OUTPUT = 'merged_data.csv'

SCRIPT_DIR = os.path.dirname(__file__)
ROOT_DIR = os.path.join(SCRIPT_DIR, "..")

PRICE = os.path.join(ROOT_DIR, "historical_prices", PRICES_FILE)
SIGNALS_DIR = os.path.join(SCRIPT_DIR, 'daily_signals')

list_of_files = glob.glob(os.path.join(SIGNALS_DIR, '??-??-??_signals.csv')) # Use YY-MM-DD format

print("Merging sentiment and price data...")

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

agent_data_path = os.path.join(SCRIPT_DIR, OUTPUT)
data.to_csv(agent_data_path, index=False)
print(f"✅ Agent data file saved to: {agent_data_path}")

