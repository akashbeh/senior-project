import pandas as pd
import matplotlib.pyplot as plt
import yfinance as yf  # You'll need to install this package
from edgar import *
from datetime import *
from pandas import *
from identity import IDENTITY

def analyze_insider_vs_price(ticker, days=180):
    """Compare insider transactions with stock price movement."""
    # Get stock price data
    end_date = datetime.today()
    start_date = end_date - timedelta(days=days)
    stock_data = yf.download(ticker, start=start_date, end=end_date)

    # Get insider transactions
    company = Company(ticker)
    form4_filings = company.get_filings(
        form="4",
        filing_date=f"{start_date.strftime('%Y-%m-%d')}:{end_date.strftime('%Y-%m-%d')}"
    )

    # Process transactions
    insider_data = []
    for filing in form4_filings:
        try:
            form4 = filing.obj()
            net_shares = form4.get_ownership_summary().net_change

            if net_shares != 0:  # Only include actual buys or sells
                insider_data.append({
                    'date': pd.to_datetime(filing.filing_date),
                    'net_shares': net_shares,
                    'transaction_type': 'BUY' if net_shares > 0 else 'SELL'
                })
        except Exception as e:
            print(f"Error processing filing: {e}")

    insider_df = pd.DataFrame(insider_data)

    # Skip plotting if we don't have both datasets
    if insider_df.empty or stock_data.empty:
        print("Insufficient data for analysis")
        return

    # Create a plot
    plt.figure(figsize=(12, 6))

    # Plot stock price
    plt.plot(stock_data.index, stock_data['Close'], label='Stock Price')

    # Mark insider transactions
    for _, row in insider_df.iterrows():
        color = 'green' if row['transaction_type'] == 'BUY' else 'red'
        marker = '^' if row['transaction_type'] == 'BUY' else 'v'
        plt.scatter(row['date'], stock_data.loc[stock_data.index >= row['date']].iloc[0]['Close'], 
                   color=color, s=100, marker=marker)

    plt.title(f'{ticker} Stock Price vs Insider Transactions')
    handles = [
        plt.Line2D([0], [0], color='blue', label='Stock Price'),
        plt.Line2D([0], [0], marker='^', color='green', linestyle='None', label='Insider Buy'),
        plt.Line2D([0], [0], marker='v', color='red', linestyle='None', label='Insider Sell')
    ]
    plt.legend(handles=handles)
    plt.grid(True)
    plt.savefig(f'{ticker}_insider_analysis.png')
    plt.close()

    return insider_df, stock_data

# Run the analysis
set_identity(IDENTITY)
print(analyze_insider_vs_price("NVDA"))
