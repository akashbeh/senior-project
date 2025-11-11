import yfinance as yf
import pandas as pd
import os
import time

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
            symbols = df[ticker_column].dropna().unique().tolist()
            clean_symbols = [s for s in symbols if s.isalpha() and s.isupper()]
            print(f"Successfully loaded {len(clean_symbols)} tickers from {screener_file}.")
            return clean_symbols
        else:
            print(f"Error: Could not find '{ticker_column}' column in {screener_file}.")
            return []
    except FileNotFoundError:
        print(f"Error: '{screener_file}' not found. Make sure it's in the root folder.")
        return []

# --- Main Execution ---
if __name__ == "__main__":
    tickers = get_nasdaq_symbols_from_local_file()
    
    if not tickers:
        print("No tickers to download. Exiting.")
        exit()
        
    print(f"Downloading max historical data for {len(tickers)} tickers in batches...")

    chunk_size = 50
    all_data_frames = []
    
    try:
        for i in range(0, len(tickers), chunk_size):
            chunk = tickers[i:i + chunk_size]
            print(f"--- Downloading Batch {i//chunk_size + 1}/{(len(tickers)//chunk_size) + 1} ({len(chunk)} tickers) ---")
            
            # --- CHANGE IS HERE ---
            # We now specify a start date instead of "max"
            data = yf.download(
                chunk, 
                start="2008-01-01", 
                interval="1d", 
                auto_adjust=False, 
                threads=False
            )
            
            if not data.empty:
                price_cols = ['Adj Close', 'Close', 'High', 'Low', 'Open', 'Volume']
                data = data.loc[:, data.columns.get_level_values(0).isin(price_cols)]
                all_data_frames.append(data)
            
            print("Sleeping for 1 second to avoid rate-limiting...")
            time.sleep(1)

        if not all_data_frames:
            print("No data was downloaded for any ticker.")
            exit()

        print("\nAll batches downloaded. Combining data...")
        full_data = pd.concat(all_data_frames, axis=1)
        
        print("Processing data...")
        
        data_long = full_data.stack(future_stack=True).reset_index()
        
        data_long.rename(columns={'level_1': 'ticker', 'Date': 'date'}, inplace=True)
        
        expected_cols = ['ticker', 'date', 'Open', 'High', 'Low', 'Close', 'Adj Close', 'Volume']
        for col in expected_cols:
            if col not in data_long.columns:
                data_long[col] = 0.0
                
        data_long = data_long[expected_cols]
        
        # Saves the file inside the 'sentiment_algo' folder
        output_file = os.path.join(os.path.dirname(__file__), 'historical_prices.csv')
        
        data_long.to_csv(output_file, index=False)
        print(f"✅ All historical price data saved to: {output_file}")

    except Exception as e:
        print(f"\nAn error occurred during download or processing: {e}")