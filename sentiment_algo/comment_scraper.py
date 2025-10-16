import praw
import pandas as pd
import time
import os
import re
from datetime import date # Import the date object

# --- Function to get NASDAQ symbols from local file ---
def get_nasdaq_symbols_from_local_file():
    """
    Reads the locally saved 'nasdaq_screener.csv' file and returns a set of symbols.
    """
    screener_file = 'nasdaq_screener.csv'
    try:
        df = pd.read_csv(screener_file)
        ticker_column = 'Symbol'
        if ticker_column in df.columns:
            print(f"Successfully loaded ticker list from {screener_file}.")
            return set(df[ticker_column].dropna().unique())
        else:
            print(f"Error: Could not find a column named '{ticker_column}' in {screener_file}.")
            return set()
    except FileNotFoundError:
        print(f"Error: '{screener_file}' not found in the project directory.")
        return set()

# --- Configuration ---
reddit = praw.Reddit("bot1")

NASDAQ_SYMBOLS = get_nasdaq_symbols_from_local_file()
if not NASDAQ_SYMBOLS:
    print("Could not load NASDAQ symbols. Exiting.")
    exit()
print(f"Loaded {len(NASDAQ_SYMBOLS)} unique NASDAQ symbols for validation.")

# CHANGE 1: Define the main data directory
output_dir = "daily_comments"
os.makedirs(output_dir, exist_ok=True) # This creates the folder if it doesn't exist

subreddit_name = 'wallstreetbets'
COMMENT_FETCH_LIMIT = 1000

# --- Data Collection ---
collected_comments = []
subreddit = reddit.subreddit(subreddit_name)
print(f"\n🔥 Fetching the latest {COMMENT_FETCH_LIMIT} comments from r/{subreddit_name}...")

ticker_regex = re.compile(r'\$[A-Z]{1,5}\b|\b[A-Z]{2,5}\b')
yester_day = time.time() - (24 * 60)

for comment in subreddit.comments(limit=COMMENT_FETCH_LIMIT):
    if comment.created_utc > yester_day:
        potential_tickers = ticker_regex.findall(comment.body)
        mentioned_stocks = set()
        for ticker in potential_tickers:
            clean_ticker = ticker.replace('$', '')
            if clean_ticker in NASDAQ_SYMBOLS:
                mentioned_stocks.add(clean_ticker)
        
        if mentioned_stocks:
            print(f"Comment number {len(collected_comments) + 1}")
            collected_comments.append({
                'timestamp': pd.to_datetime(comment.created_utc, unit='s'),
                'comment_id': comment.id,
                'comment_body': comment.body,
                'mentioned_stocks': list(mentioned_stocks)
            })

print(f"✅ Found {len(collected_comments)} comments mentioning valid NASDAQ stocks from the last 24 hours.")

# --- Save to a new daily file ---
if collected_comments:
    df_comments = pd.DataFrame(collected_comments)
    df_exploded = df_comments.explode('mentioned_stocks').rename(columns={'mentioned_stocks': 'ticker'})

    # CHANGE 2: Generate filename based on today's date
    today_str = date.today().strftime('%y-%m-%d') 
    output_filename = (f"{today_str}.csv")
    output_path = os.path.join(output_dir, output_filename)
    
    # CHANGE 3: Save to the new, date-stamped file
    # We no longer need to append (mode='a') since each day gets its own file.
    df_exploded.to_csv(output_path, index=False)
    
    print(f"💾 Data saved to: {output_path}")
else:
    print("No new relevant comments to save.")