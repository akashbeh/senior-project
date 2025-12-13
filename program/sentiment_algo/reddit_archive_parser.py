import zstandard as zstd
import pandas as pd
import json
import os
import re
import io
from datetime import datetime, timezone
from pysentimiento import create_analyzer
import numpy as np

# --- Configuration ---
SCRIPT_DIR = os.path.dirname(__file__)
PROJECT_ROOT = os.path.join(SCRIPT_DIR, "..")
DATA_DIR = os.path.join(PROJECT_ROOT, "..")
ZST_DIR = os.path.join(DATA_DIR, "reddit-archive")

PRICE_FILE = os.path.join(SCRIPT_DIR, 'historical_prices', 'historical_prices.csv')
SCREENER_FILE = os.path.join(DATA_DIR, 'nasdaq_screener.csv')
OUTPUT_FILE = os.path.join(SCRIPT_DIR, 'merged_data.csv')
CHECKPOINT_FILE = os.path.join(SCRIPT_DIR, 'temp_raw_extracted_sentiment.csv')

# Banned words to ignore (Common English words that look like tickers)
BANNED_LIST = {'AI', 'FOR', 'IT', 'GF', 'OP', 'YOU', 'WAY', 'ARE', 'CAN', 'NOW', 'OUT', 'SEE', 'ONE', 'ALL', 'NEW', 'HAS', 'BIG', 'GO', 'UK'}

print("--- Starting Historical Data Processing & Append Pipeline ---")

# --- 1. Load Tickers ---
def get_nasdaq_symbols():
    try:
        df = pd.read_csv(SCREENER_FILE)
        if 'Symbol' in df.columns:
            all_symbols = set(df['Symbol'].dropna().unique())
            # Ensure tickers are valid and not in banned list
            valid_symbols = {s for s in all_symbols if s not in BANNED_LIST and s.isalpha()}
            print(f"Loaded {len(valid_symbols)} valid tickers.")
            return valid_symbols
    except Exception as e:
        print(f"Error loading tickers: {e}")
        return set()

NASDAQ_SYMBOLS = get_nasdaq_symbols()

# --- NEW: Simplified Regex ---
# Finds "$AAPL" or just "AAPL". We rely on the BANNED_LIST to filter noise.
ticker_regex = re.compile(r'\b\$?([A-Z]{2,5})\b')

# --- 2. Initialize Sentiment Analyzer ---
print("Initializing BERTweet analyzer...")
analyzer = create_analyzer(task="sentiment", lang="en")

def calculate_sentiment(text):
    if not text: return 0.0
    try:
        res = analyzer.predict(text)
        return (res.probas['POS'] + 0.5 * res.probas['NEU']) - 0.5
    except:
        return 0.0

# --- 3. Process ZST Files ---
def process_zst_files():
    if os.path.exists(CHECKPOINT_FILE):
        print(f"Found checkpoint file: {CHECKPOINT_FILE}")
        user_input = input("Do you want to load from checkpoint? (y/n): ").lower()
        if user_input == 'y':
            print("Loading checkpoint...")
            return pd.read_csv(CHECKPOINT_FILE, parse_dates=['timestamp'])

    processed_data = []
    
    if not os.path.exists(ZST_DIR):
        print(f"Error: Data directory not found at {ZST_DIR}")
        return pd.DataFrame()

    zst_files = [f for f in os.listdir(ZST_DIR) if f.endswith('.zst')]
    if not zst_files:
        print(f"No .zst files found in {ZST_DIR}.")
        return pd.DataFrame()

    print(f"Found {len(zst_files)} archive files. Starting extraction...")

    for zst_file in zst_files:
        file_path = os.path.join(ZST_DIR, zst_file)
        print(f"Processing {zst_file}...")
        
        match_count = 0
        
        with open(file_path, 'rb') as fh:
            dctx = zstd.ZstdDecompressor()
            with dctx.stream_reader(fh) as reader:
                text_stream = io.TextIOWrapper(reader, encoding='utf-8')
                
                count = 0
                for line in text_stream:
                    count += 1
                    # Status update every 5000 lines
                    if count % 5000 == 0:
                        print(f"  Scanned: {count} | Matches Found: {match_count} ...", end='\r')
                        
                    try:
                        obj = json.loads(line)
                        
                        # --- FIX: Check ALL text fields (Title, Body, Selftext) ---
                        parts = [obj.get('title', ''), obj.get('selftext', ''), obj.get('body', '')]
                        # Join them, filter out None/Deleted, convert to upper case for regex
                        body = " ".join([p for p in parts if p and p != '[deleted]' and p != '[removed]'])
                        
                        if not body.strip():
                            continue
                        
                        # Find tickers
                        found_tickers = set()
                        # Use regex to find potential tickers
                        matches = ticker_regex.findall(body) # Returns list of groups (the ticker text)
                        
                        for match in matches:
                            clean = match.replace('$', '')
                            if clean in NASDAQ_SYMBOLS:
                                found_tickers.add(clean)
                        
                        if found_tickers:
                            match_count += 1
                            sentiment = calculate_sentiment(body)
                            created_utc = int(obj.get('created_utc', 0))
                            # Use timezone-aware UTC
                            dt = datetime.fromtimestamp(created_utc, timezone.utc)
                            
                            for ticker in found_tickers:
                                processed_data.append({
                                    'timestamp': dt,
                                    'ticker': ticker,
                                    'sentiment_score': sentiment
                                })
                    except Exception:
                        continue
        print(f"\nFinished {zst_file}. Total matches: {match_count}")

    df = pd.DataFrame(processed_data)
    
    if not df.empty:
        print(f"Saving checkpoint to {CHECKPOINT_FILE}...")
        df.to_csv(CHECKPOINT_FILE, index=False)
        
    return df

# --- 4. Generate SVC Signals ---
def generate_signals(df):
    print("Aggregating sentiment and generating SVC signals...")
    # Remove timezone info for simpler merging
    df['timestamp'] = pd.to_datetime(df['timestamp']).dt.tz_localize(None)
    df = df.sort_values('timestamp')
    
    # Aggregate daily
    daily_stats = df.groupby(['ticker', pd.Grouper(key='timestamp', freq='D')]).agg(
        mean_sentiment=('sentiment_score', 'mean'),
        comment_count=('sentiment_score', 'count')
    ).reset_index()
    
    daily_stats.set_index('timestamp', inplace=True)
    
    def calculate_svc(group):
        group = group.sort_index()
        group['sentiment_change'] = group['mean_sentiment'].diff()
        group['volume_change'] = group['comment_count'].diff().abs()
        group['svc'] = group['sentiment_change'] * group['volume_change']
        return group

    # Pandas 2.2+ fix for groupby apply
    try:
        final_signals = daily_stats.groupby('ticker', include_groups=False).apply(calculate_svc)
    except TypeError:
        final_signals = daily_stats.groupby('ticker').apply(calculate_svc)

    if 'ticker' in final_signals.columns:
        final_signals = final_signals.drop(columns=['ticker'])
        
    final_signals = final_signals.reset_index()
    final_signals.rename(columns={'timestamp': 'date'}, inplace=True)
    final_signals.replace([np.inf, -np.inf], np.nan, inplace=True)
    final_signals.fillna(0, inplace=True)
    
    return final_signals

# --- 5. Engineer Price Features ---
def engineer_prices():
    print("Loading and engineering historical price features...")
    try:
        prices_df = pd.read_csv(PRICE_FILE, parse_dates=['date'])
    except FileNotFoundError:
        print("Historical prices file not found.")
        return pd.DataFrame()

    if 'Ticker' in prices_df.columns:
        prices_df.rename(columns={'Ticker': 'ticker'}, inplace=True)
        
    prices_df.sort_values(by=['ticker', 'date'], inplace=True)
    
    periods = {
        'change_day': 1, 'change_week': 5, 'change_month': 21,
        'change_3mo': 63, 'change_6mo': 126, 'change_9mo': 189, 'change_1yr': 252
    }

    # Use fill_method=None to avoid FutureWarnings
    for name, period in periods.items():
        prices_df[name] = prices_df.groupby('ticker')['Adj Close'].pct_change(periods=period, fill_method=None)

    prices_df['next_day_pct_change'] = prices_df.groupby('ticker')['Adj Close'].pct_change(periods=-1, fill_method=None).shift(1)
    
    HOLD_THRESHOLD = 0.02
    def create_target(pct_change):
        if pct_change > HOLD_THRESHOLD: return 1
        elif pct_change < -HOLD_THRESHOLD: return -1
        else: return 0

    prices_df['target'] = prices_df['next_day_pct_change'].apply(create_target)
    
    return prices_df

# --- 6. Main Logic ---
if __name__ == "__main__":
    # A. Process Archives
    raw_sentiment_df = process_zst_files()
    
    if raw_sentiment_df.empty:
        print("No data extracted from archives. Please check your logic or files.")
        exit()
        
    # B. Generate Signals
    historical_signals = generate_signals(raw_sentiment_df)
    print(f"Generated {len(historical_signals)} historical signal points.")
    
    # C. Engineer Prices
    price_features_df = engineer_prices()
    if price_features_df.empty:
        exit()
        
    # D. Merge
    print("Merging historical signals with price data...")
    historical_signals['ticker'] = historical_signals['ticker'].astype(str)
    price_features_df['ticker'] = price_features_df['ticker'].astype(str)
    
    merged_data = pd.merge(
        price_features_df,
        historical_signals,
        on=['ticker', 'date'],
        how='inner'
    )
    
    merged_data.dropna(inplace=True)
    print(f"New historical dataset size: {len(merged_data)} rows.")
    
    # E. Save
    merged_data.to_csv(OUTPUT_FILE, index=False)
    print(f"✅ Created new full dataset at: {OUTPUT_FILE}")
    print(f"Total rows: {len(merged_data)}")

