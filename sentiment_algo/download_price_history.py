import yfinance as yf
import pandas as pd
import os
import time
import numpy as np

def get_nasdaq_symbols_from_local_file():
    """
    Reads the locally saved 'nasdaq_screener.csv' file from the parent directory
    and returns a clean list of symbols.
    """
    screener_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'nasdaq_screener.csv')
    
    try:
        df = pd.read_csv(screener_path)
        ticker_column = 'Symbol'
        if ticker_column in df.columns:
            symbols = df[ticker_column].dropna().unique().tolist()
            clean_symbols = [s for s in symbols if s.isalpha() and s.isupper()]
            print(f"Successfully loaded {len(clean_symbols)} tickers from {screener_path}.")
            return clean_symbols
        else:
            print(f"Error: Could not find '{ticker_column}' column in {screener_path}.")
            return []
    except FileNotFoundError:
        print(f"Error: '{screener_path}' not found. Make sure it's in the root folder.")
        return []

# --- Main Execution ---
if __name__ == "__main__":
    tickers = get_nasdaq_symbols_from_local_file()
    
    if not tickers:
        print("No tickers to download. Exiting.")
        exit()
        
    print(f"Downloading historical data for {len(tickers)} tickers from 2008-01-01 to present...")

    chunk_size = 50
    all_data_frames = [] 
    
    try:
        for i in range(0, len(tickers), chunk_size):            
            chunk = tickers[i:i + chunk_size]
            print(f"--- Downloading Batch {i//chunk_size + 1}/{(len(tickers)//chunk_size) + 1} ({len(chunk)} tickers) ---")
            
            data = yf.download(
                chunk, 
                start="2008-01-01", 
                interval="1d", 
                auto_adjust=False, 
                threads=False 
            )
            
            if data.empty:
                print("No data for this batch, skipping.")
                continue

            # --- Process data *inside* the loop ---
            price_cols = ['Adj Close', 'Close', 'High', 'Low', 'Open', 'Volume']
            data = data.loc[:, data.columns.get_level_values(0).isin(price_cols)]
            
            # --- FIX 1: Removed dropna=False ---
            data_long_chunk = data.stack(future_stack=True).reset_index()
            
            # Rename columns
            data_long_chunk.rename(columns={'level_1': 'Ticker', 'Date': 'date'}, inplace=True)
            
            # --- FIX 2: Filter out bad ticker rows (like '0.0') ---
            # Keep only rows where the 'ticker' is in our original requested list
            data_long_chunk = data_long_chunk[data_long_chunk['Ticker'].isin(chunk)]
            
            all_data_frames.append(data_long_chunk)
            
            print("Sleeping for 1 second to avoid rate-limiting...")
            time.sleep(1)

        if not all_data_frames:
            print("No data was downloaded for any ticker.")
            exit()

        print("\nAll batches downloaded. Combining all processed chunks...")
        full_data = pd.concat(all_data_frames, ignore_index=True)
        
        print("Cleaning processed data...")
        
        expected_cols = ['Ticker', 'date', 'Open', 'High', 'Low', 'Close', 'Adj Close', 'Volume']
        
        for col in expected_cols:
            if col not in full_data.columns:
                full_data[col] = np.nan
                
        # --- FIX 3: Remove rows where all price data is missing ---
        # This removes the "0.0,2008-01-02,,,,,,," rows
        full_data.dropna(subset=['Open', 'High', 'Low', 'Close', 'Volume'], how='all', inplace=True)
        
        full_data = full_data[expected_cols]
        
        output_file = os.path.join(os.path.dirname(__file__), 'historical_prices.csv')
        
        full_data.to_csv(output_file, index=False)
        print(f"✅ All historical price data from 2008 saved to: {output_file}")

    except Exception as e:
        print(f"\nAn error occurred during download or processing: {e}")