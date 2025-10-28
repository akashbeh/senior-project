import requests
import time
import re
from typing import List, Dict

def fetch_all_tweets(query: str, api_key: str) -> List[Dict]:
    """
    Fetches all tweets matching the given query from Twitter API, handling deduplication.

    Args:
        query (str): The search query for tweets
        api_key (str): Twitter API key for authentication

    Returns:
        List[Dict]: List of unique tweets matching the query

    Notes:
        - Handles pagination using cursor and max_id parameters
        - Deduplicates tweets based on tweet ID to handle max_id overlap
        - Implements rate limiting handling
        - Continues fetching beyond Twitter's initial 800-1200 tweet limit
        - Includes error handling for API failures
    """
    base_url = "https://api.twitterapi.io/twitter/tweet/advanced_search"
    headers = {"x-api-key": api_key}
    all_tweets = []
    seen_tweet_ids = set()  # Set to track unique tweet IDs
    cursor = None
    last_min_id = None
    max_retries = 3

    while True:
        # Prepare query parameters
        params = {
            "query": query,
            "queryType": "Latest"
        }

        # Add cursor if available (for regular pagination)
        if cursor:
            params["cursor"] = cursor
        elif last_min_id:
            # Add max_id if available (for fetching beyond initial limit)
            params["query"] = f"{query} max_id:{last_min_id}"

        retry_count = 0
        while retry_count < max_retries:
            try:
                # Make API request
                response = requests.get(base_url, headers=headers, params=params)
                response.raise_for_status()  # Raise exception for bad status codes
                data = response.json()

                # Extract tweets and metadata
                tweets = data.get("tweets", [])
                has_next_page = data.get("has_next_page", False)
                cursor = data.get("next_cursor", None)

                # Filter out duplicate tweets
                new_tweets = [tweet for tweet in tweets if tweet.get("id") not in seen_tweet_ids]
                
                # Add new tweet IDs to the set and tweets to the collection
                for tweet in new_tweets:
                    seen_tweet_ids.add(tweet.get("id"))
                    all_tweets.append(tweet)

                # If no new tweets and no next page, break the loop
                if not new_tweets and not has_next_page:
                    return all_tweets

                # Update last_min_id from the last tweet if available
                if new_tweets:
                    last_min_id = new_tweets[-1].get("id")

                # If no next page but we have new tweets, try with max_id
                if not has_next_page and new_tweets:
                    cursor = None  # Reset cursor for max_id pagination
                    break

                # If has next page, continue with cursor
                if has_next_page:
                    break

            except requests.exceptions.RequestException as e:
                retry_count += 1
                if retry_count == max_retries:
                    print(f"Failed to fetch tweets after {max_retries} attempts: {str(e)}")
                    return all_tweets

                # Handle rate limiting
                if hasattr(response, 'status_code') and response.status_code == 429:
                    #For users in the free trial period, the QPS is very low—only one API request can be made every 5 seconds. Once you complete the recharge, the QPS limit will be increased to 20.
                    print("Rate limit reached. Waiting for 1 second...")
                    time.sleep(1)  # Wait 1 second for rate limit reset
                else:
                    print(f"Error occurred: {str(e)}. Retrying {retry_count}/{max_retries}")
                    time.sleep(2 ** retry_count)  # Exponential backoff

        # If no more pages and no new tweets with max_id, we're done
        if not has_next_page and not new_tweets:
            break

    return all_tweets

# Example usage
if __name__ == "__main__":
    api_key = "new1_100efdfda2834c94b8e7f622c9d73456"

    # Get input from the user
    keywords = input("Enter the keywords you want to search for: ").strip()
    user = input("Enter user you want to search for (or leave blank): ").strip()
    since_date = input("Enter your query start date (YYYY-MM-DD, optional): ").strip()
    until_date = input("Enter your query end date (YYYY-MM-DD, optional): ").strip()

    # Build the query string
    query_parts = []
    if keywords:
        query_parts.append(keywords)
    if user:
        query_parts.append(f"from:{user}")
    if since_date:
        query_parts.append(f"since:{since_date}")
    if until_date:
        query_parts.append(f"until:{until_date}")

    query = " ".join(query_parts) + "-grok"
    
    # Save file
    import json
    def safe_filename(query: str) -> str:
        return re.sub(r'[^a-zA-Z0-9_-]+', '_', query)[:50] 

    #filename built 
    filename = f"{safe_filename(query)}.json"

    #fetch tweets
    tweets = fetch_all_tweets(query, api_key)
    print(f"Fetched {len(tweets)} unique tweets")

    #print and save file if tweets found. if not, nothing saved
    if tweets:
        with open(filename, "w", encoding="utf-8") as f:
         json.dump(tweets, f, indent=2, ensure_ascii=False)
        print(f"Saved tweets to {filename}")
    else:
        print("No tweets found — no file created.")