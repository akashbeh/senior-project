import praw
import pandas as pd
import time
import os
import re
from datetime import date

# --- Function to get NASDAQ symbols from local file ---
screener_file = 'nasdaq_screener.csv'
screener_path = os.path.join(os.path.dirname(__file__), '..', 'data', screener_file)
def get_nasdaq_symbols_from_local_file():
    try:
        df = pd.read_csv(screener_path)
        ticker_column = 'Symbol'
        if ticker_column in df.columns:
            return set(df[ticker_column].dropna().unique())
        else:
            print(f"Error: Could not find '{ticker_column}' column in {screener_file}.")
            return set()
    except FileNotFoundError:
        print(f"Error: '{screener_file}' not found.")
        return set()

# --- Configuration ---
reddit = praw.Reddit("bot1")

NASDAQ_SYMBOLS = get_nasdaq_symbols_from_local_file()
if not NASDAQ_SYMBOLS:
    print("Could not load NASDAQ symbols. Exiting.")
    exit()
# print(f"Loaded {len(NASDAQ_SYMBOLS)} unique NASDAQ symbols.") # Less verbose

output_dir = "daily_comments"
os.makedirs(output_dir, exist_ok=True)


SUBREDDIT_LIST = ['wallstreetbets', 'stocks', 'investing', 'StockMarket', 'personalfinance']
COMMENT_FETCH_LIMIT_PER_SUB = 1000

# --- Data Collection ---
collected_comments = []
banned_list = ['AI', 'FOR', 'IT', 'GF', 'OP', 'YOU', 'WAY', 'USA', 'IQ']
print(f"🔥 Starting comment collection from: {', '.join(SUBREDDIT_LIST)}")

ticker_regex = re.compile(r'(?<!\b[A-Z]{2}\s)(?<!\b[A-Z]{3}\s)(?<!\b[A-Z]{4}\s)(?<!\b[A-Z]{5}\s)(\b(?:\$[A-Z]{1,5}|[A-Z]{2,5})\b)(?!\s[A-Z]{2,}\b)')
yester_day = time.time() - (24 * 60 * 60)
total_fetched_overall = 0 # To track total comments checked across all subs

for subreddit_name in SUBREDDIT_LIST:
    try:
        subreddit = reddit.subreddit(subreddit_name)
        print(f"   Fetching from r/{subreddit_name} (limit={COMMENT_FETCH_LIMIT_PER_SUB})...")
        count_for_sub = 0
        fetched_in_sub = 0
        for comment in subreddit.comments(limit=COMMENT_FETCH_LIMIT_PER_SUB):
            fetched_in_sub += 1
            if comment.created_utc > yester_day:
                potential_tickers = ticker_regex.findall(comment.body)
                mentioned_stocks = set()
                for ticker in potential_tickers:
                    clean_ticker = ticker.replace('$', '')
                    # Check against NASDAQ list AND banned list
                    if clean_ticker in NASDAQ_SYMBOLS and clean_ticker not in banned_list:
                        mentioned_stocks.add(clean_ticker)

                if mentioned_stocks:
                    collected_comments.append({
                        'timestamp': pd.to_datetime(comment.created_utc, unit='s'),
                        'comment_id': comment.id,
                        'comment_body': comment.body,
                        'mentioned_stocks': list(mentioned_stocks),
                        'subreddit': subreddit_name 
                    })
                    count_for_sub += 1
        total_fetched_overall += fetched_in_sub
        print(f"      Checked {fetched_in_sub} comments, found {count_for_sub} relevant comments in r/{subreddit_name}.")

    except Exception as e:
        # Catch potential errors like private subreddits or API issues
        print(f"      Could not fetch from r/{subreddit_name}. Error: {e}")

print(f"\n✅ Total comments checked across all subreddits: {total_fetched_overall}")
print(f"✅ Found {len(collected_comments)} relevant comments across all subreddits from the last 24 hours.")

# --- Save to a new daily file ---
if collected_comments:
    df_comments = pd.DataFrame(collected_comments)
    # Explode and rename as before
    df_exploded = df_comments.explode('mentioned_stocks').rename(columns={'mentioned_stocks': 'ticker'})

    today_str = date.today().strftime('%y-%m-%d')
    output_filename = f"{today_str}.csv"
    output_path = os.path.join(output_dir, output_filename)

    df_exploded.to_csv(output_path, index=False)
    print(f"💾 Data saved to: {output_path}")
else:
    print("No new relevant comments to save.")