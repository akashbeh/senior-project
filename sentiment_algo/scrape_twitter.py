import requests
import pandas as pd
import time
import re
from typing import List, Dict
import json
import os
from datetime import date, timedelta

# --- Configuration ---
API_KEY = "new1_100efdfda2834c94b8e7f622c9d73456"

# List of high-profile/trustworthy sources
TRUSTED_SOURCES = [
    "CNBC", "Bloomberg", "Reuters", "FinancialTimes", "WSJ",
    "MarketWatch", "Stocktwits", "jimcramer", "elonmusk"
]

# Output folder for daily, date-stamped CSVs
SCRIPT_DIR = os.path.dirname(__file__)

# Save output to "sentiment_algo/daily_tweets" in the project root
OUTPUT_DIR = os.path.join(SCRIPT_DIR, "daily_tweets")
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Banned word list (from your comment_scraper.py)
BANNED_LIST = {'AI', 'FOR', 'IT', 'GF', 'OP', 'YOU', 'WAY'}

# --- Function to get NASDAQ symbols (from your comment_scraper.py) ---
def get_nasdaq_symbols_from_local_file():
    """
    Reads the locally saved 'nasdaq_screener.csv' file and returns a
    clean list of symbols.
    """
    screener_file = 'nasdaq_screener.csv'
    screener_path = os.path.join(os.path.dirname(__file__), '..', 'data', screener_file)
    try:
        df = pd.read_csv(screener_path)
        ticker_column = 'Symbol'
        if ticker_column in df.columns:
            all_symbols = set(df[ticker_column].dropna().unique())
            valid_symbols = {s for s in all_symbols if s not in BANNED_LIST and s.isalpha()}
            return list(valid_symbols) # Return as a list for chunking
        else:
            print(f"Error: Could not find '{ticker_column}' column in {screener_file}.")
            return []
    except FileNotFoundError:
        print(f"Error: '{screener_path}' not found.")
        return []

def chunk_list(data, chunk_size):
    """Yield successive n-sized chunks from a list."""
    for i in range(0, len(data), chunk_size):
        yield data[i:i + chunk_size]

# --- Original fetch_all_tweets function from your script ---
def fetch_all_tweets(query: str, api_key: str) -> List[Dict]:
    """
    Fetches all tweets matching the given query from Twitter API, handling deduplication.
    (This function is from your tw_scraper_v1.py)
    """
    base_url = "https://api.twitterapi.io/twitter/tweet/advanced_search"
    headers = {"x-api-key": api_key}
    all_tweets = []
    seen_tweet_ids = set()
    cursor = None
    last_min_id = None
    max_retries = 3

    while True:
        params = {"query": query, "queryType": "Latest"}
        if cursor:
            params["cursor"] = cursor
        elif last_min_id:
            params["query"] = f"{query} max_id:{last_min_id}"

        retry_count = 0
        response = None # Define response here to check in finally
        
        while retry_count < max_retries:
            try:
                response = requests.get(base_url, headers=headers, params=params)
                response.raise_for_status()
                data = response.json()

                tweets = data.get("tweets", [])
                has_next_page = data.get("has_next_page", False)
                cursor = data.get("next_cursor", None)

                new_tweets = [tweet for tweet in tweets if tweet.get("id") not in seen_tweet_ids]
                
                for tweet in new_tweets:
                    seen_tweet_ids.add(tweet.get("id"))
                    all_tweets.append(tweet)

                if not new_tweets and not has_next_page:
                    return all_tweets

                if new_tweets:
                    last_min_id = new_tweets[-1].get("id")

                if not has_next_page and new_tweets:
                    cursor = None
                    break

                if has_next_page:
                    break

            except requests.exceptions.RequestException as e:
                retry_count += 1
                if retry_count == max_retries:
                    print(f"Failed to fetch tweets after {max_retries} attempts: {str(e)}")
                    return all_tweets

                if hasattr(response, 'status_code') and response.status_code == 429:
                    print("Rate limit reached. Waiting for 5 seconds...")
                    time.sleep(5) 
                else:
                    print(f"Error occurred: {str(e)}. Retrying {retry_count}/{max_retries}")
                    time.sleep(2 ** retry_count)

        if not has_next_page and not new_tweets:
            break
            
    return all_tweets

# --- Main execution logic ---
def run_daily_scrape():
    """Fetches tweets for all tickers from trusted sources."""
    
    tickers = get_nasdaq_symbols_from_local_file()
    if not tickers:
        print("No tickers loaded, stopping scraper.")
        return
    
    # Define query constants
    sources_query = " OR ".join([f"from:{source}" for source in TRUSTED_SOURCES])
    since_date = (date.today() - timedelta(days=1)).strftime('%Y-%m-%d')
    
    # Chunk tickers to keep queries manageable
    ticker_chunks = list(chunk_list(tickers, 30))
    master_tweet_list = []
    
    print(f"🔥 Starting tweet collection for {len(tickers)} tickers across {len(ticker_chunks)} chunks...")

    for i, chunk in enumerate(ticker_chunks):
        print(f"\n--- Processing Chunk {i+1}/{len(ticker_chunks)} ---")
        
        tickers_query = " OR ".join(chunk)
        # Build the final query for this chunk
        query = f"({tickers_query}) ({sources_query}) since:{since_date}"
        
        print(f"Querying for: {query[:150]}...") # Print start of query
        
        chunk_tweets = fetch_all_tweets(query, API_KEY)
        print(f"Fetched {len(chunk_tweets)} unique tweets for this chunk.")
        
        if chunk_tweets:
            master_tweet_list.extend(chunk_tweets)

    # --- Process and Save All Found Tweets ---
    print(f"\n--- All chunks processed ---")
    print(f"Fetched {len(master_tweet_list)} total unique tweets.")
    
    if master_tweet_list:
        # Deduplicate one last time, just in case of overlap
        final_seen_ids = set()
        final_tweet_list = []
        for tweet in master_tweet_list:
            if tweet.get("id") not in final_seen_ids:
                final_seen_ids.add(tweet.get("id"))
                final_tweet_list.append(tweet)

        print(f"Saving {len(final_tweet_list)} unique tweets...")
        
        # Convert to DataFrame for easier saving
        df = pd.DataFrame(final_tweet_list)
        
        # Create daily, date-stamped filename
        today_str = date.today().strftime('%y-%m-%d')
        output_filename = f"{today_str}.csv"
        output_path = os.path.join(OUTPUT_DIR, output_filename)
        
        df.to_csv(output_path, index=False, encoding='utf-8')
        print(f"💾 Data saved to: {output_path}")
    else:
        print("No tweets found — no file created.")

if __name__ == "__main__":
    if API_KEY == "PASTE_YOUR_NEW_KEY_FROM_api.twitterapi.io_HERE":
        print("Error: API_KEY not set. Please edit the script and add your api.twitterapi.io key.")
    else:
        run_daily_scrape()
