from pysentimiento import create_analyzer
import pandas as pd
from datetime import date
import os
import re

# --- Setup Paths ---
SCRIPT_DIR = os.path.dirname(__file__)
PROJECT_ROOT = os.path.join(SCRIPT_DIR, "..")

REDDIT_INPUT_DIR = os.path.join(PROJECT_ROOT, 'sentiment_algo', "daily_comments")
TWITTER_INPUT_DIR = os.path.join(PROJECT_ROOT,'sentiment_algo', "daily-tweets")
OUTPUT_DIR = os.path.join(PROJECT_ROOT, 'sentiment_algo', "daily_sentiment")
os.makedirs(OUTPUT_DIR, exist_ok=True)

# --- NASDAQ & Banned List Setup (Needed to find tickers in tweets) ---
BANNED_LIST = {'AI', 'FOR', 'IT', 'GF', 'OP', 'YOU', 'WAY'}

def get_nasdaq_symbols_from_local_file():
    screener_path = os.path.join(PROJECT_ROOT, 'data', 'nasdaq_screener.csv')
    try:
        df = pd.read_csv(screener_path)
        ticker_column = 'Symbol'
        if ticker_column in df.columns:
            all_symbols = set(df[ticker_column].dropna().unique())
            valid_symbols = {s for s in all_symbols if s not in BANNED_LIST and s.isalpha()}
            return valid_symbols
        else:
            print(f"Error: Could not find '{ticker_column}' column in {screener_path}.")
            return set()
    except FileNotFoundError:
        print(f"Error: '{screener_path}' not found.")
        return set()

NASDAQ_SYMBOLS = get_nasdaq_symbols_from_local_file()
# Regex from your Reddit scraper
ticker_regex = re.compile(r'(?<!\b[A-Z]{2}\s)(?<!\b[A-Z]{3}\s)(?<!\b[A-Z]{4}\s)(?<!\b[A-Z]{5}\s)(\b(?:\$[A-Z]{1,5}|[A-Z]{2,5})\b)(?!\s[A-Z]{2,}\b)')

# --- Determine today's date ---
today_str = date.today().strftime('%y-%m-%d')
output_file = os.path.join(OUTPUT_DIR, f"{today_str}.csv")

# --- Analyzer Setup ---
print("Setting up the sentiment analyzer...")
analyzer = create_analyzer(task="sentiment", lang="en")
print("Analyzer is ready.")

# --- Sentiment Calculation Function ---
def calculate_sentiment_score(text):
    if not isinstance(text, str) or not text.strip():
        return 0.0
    result = analyzer.predict(text)
    pos_score = result.probas['POS']
    neu_score = result.probas['NEU']
    sentiment_score = (pos_score + 0.5 * neu_score) - 0.5
    return sentiment_score

# --- Main Processing ---
all_processed_data = []

# 1. Process Reddit Comments
try:
    reddit_input_file = os.path.join(REDDIT_INPUT_DIR, f"{today_str}.csv")
    df_reddit = pd.read_csv(reddit_input_file)
    print(f"Successfully loaded {len(df_reddit)} comment entries from {reddit_input_file}")
    
    print("Calculating sentiment for Reddit comments...")
    df_reddit['sentiment_score'] = df_reddit['comment_body'].apply(calculate_sentiment_score)
    df_reddit['source'] = 'reddit'
    df_reddit.rename(columns={'comment_body': 'text'}, inplace=True)
    all_processed_data.append(df_reddit)
    
except FileNotFoundError:
    print(f"Warning: Reddit file '{reddit_input_file}' not found. Skipping.")
except Exception as e:
    print(f"Error processing Reddit file: {e}")

# 2. Process Twitter Tweets
try:
    twitter_input_file = os.path.join(TWITTER_INPUT_DIR, f"{today_str}.csv")
    df_twitter = pd.read_csv(twitter_input_file)
    print(f"Successfully loaded {len(df_twitter)} tweet entries from {twitter_input_file}")

    # --- TIMESTAMP FIX ---
    # Check for 'createdAt' and rename it to 'timestamp'
    if 'createdAt' in df_twitter.columns and 'timestamp' not in df_twitter.columns:
        print("Found 'createdAt' column, renaming to 'timestamp'.")
        df_twitter.rename(columns={'createdAt': 'timestamp'}, inplace=True)
    
    # Define the exact format of the Twitter timestamp
    twitter_time_format = "%a %b %d %H:%M:%S %z %Y"
    # Convert the column, coercing any errors to NaT (Not a Time)
    df_twitter['timestamp'] = pd.to_datetime(df_twitter['timestamp'], format=twitter_time_format, errors='coerce')
    
    # Drop any rows that failed to parse (e.g., header, footer, or bad data)
    original_count = len(df_twitter)
    df_twitter.dropna(subset=['timestamp'], inplace=True)
    new_count = len(df_twitter)
    if original_count > new_count:
        print(f"Dropped {original_count - new_count} tweets with invalid timestamps.")
    # --- END FIX ---
    
    print("Calculating sentiment for tweets...")
    df_twitter['sentiment_score'] = df_twitter['text'].apply(calculate_sentiment_score)
    df_twitter['source'] = 'twitter'
    
    # Re-find tickers in tweets
    def find_tickers_in_tweet(tweet_text):
        if not isinstance(tweet_text, str):
            return pd.NA
        potential_tickers = ticker_regex.findall(tweet_text.upper())
        mentioned_stocks = set()
        for ticker in potential_tickers:
            clean_ticker = ticker.replace('$', '')
            if clean_ticker in NASDAQ_SYMBOLS:
                mentioned_stocks.add(clean_ticker)
        return list(mentioned_stocks) if mentioned_stocks else pd.NA

    df_twitter['mentioned_stocks'] = df_twitter['text'].apply(find_tickers_in_tweet)
    df_twitter.dropna(subset=['mentioned_stocks'], inplace=True) # Drop tweets that didn't mention a valid ticker
    df_twitter = df_twitter.explode('mentioned_stocks').rename(columns={'mentioned_stocks': 'ticker'})
    
    all_processed_data.append(df_twitter)
    
except FileNotFoundError:
    print(f"Warning: Twitter file '{twitter_input_file}' not found. Skipping.")
except Exception as e:
    print(f"Error processing Twitter file: {e}")

# --- 3. Combine and Save ---
if all_processed_data:
    final_df = pd.concat(all_processed_data, ignore_index=True)
    
    # Standardize column name (some scrapers might use 'id')
    if 'tweet_id' in final_df.columns:
        final_df.rename(columns={'tweet_id': 'comment_id'}, inplace=True)
    if 'id' in final_df.columns and 'comment_id' not in final_df.columns:
         final_df.rename(columns={'id': 'comment_id'}, inplace=True)

    # Select only the columns we need for the next step
    columns_to_keep = ['timestamp', 'ticker', 'sentiment_score', 'source', 'comment_id', 'text']
    
    # Ensure all needed columns are present
    for col in columns_to_keep:
        if col not in final_df.columns:
            final_df[col] = pd.NA
    
    final_df = final_df[columns_to_keep]
    
    final_df.to_csv(output_file, index=False)
    print(f"\n✅ Combined sentiment data saved to: {output_file}")
else:
    print("\nNo data processed from any source. No file saved.")