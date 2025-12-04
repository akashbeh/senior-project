# Insider Trading Tracker

A Python application to track insider trading activities and correlate them with stock performance using yfinance and SEC EDGAR data.

## Overview

This project combines:
- **yfinance**: For real-time stock prices, historical data, and company information
- **SEC EDGAR API**: For official insider trading filings (Form 4)

## Important Note

`yfinance` doesn't provide insider trading data directly. Insider trading information comes from SEC Form 4 filings, which must be retrieved from the SEC's EDGAR database.

## Setup

1. **Install dependencies**:
```bash
pip install -r requirements.txt
```

2. **Update User-Agent in `sec_insider_data.py`**:
   - The SEC requires a valid User-Agent header
   - Replace `"YourName your.email@example.com"` with your actual name and email

## Usage

### Basic Example

```python
from insider_tracker import InsiderTradingTracker

tracker = InsiderTradingTracker()

# Get company information
info = tracker.get_company_info("AAPL")
print(info)

# Get stock data
stock_df = tracker.get_stock_data("AAPL", "2024-01-01", "2024-12-31")
print(stock_df.head())

# Track multiple stocks
tickers = ["AAPL", "MSFT", "GOOGL", "TSLA"]
results = tracker.track_multiple_stocks(tickers)
```

### SEC Insider Data Example

```python
from sec_insider_data import SECInsiderData

# Initialize with your contact info (required by SEC)
sec = SECInsiderData(user_agent="Your Name your.email@example.com")

# Get insider transactions
insider_df = sec.get_insider_transactions("AAPL", max_filings=20)
print(insider_df)
```

## Features

### Current
- ✅ Fetch stock data using yfinance
- ✅ Get company information
- ✅ Retrieve Form 4 filings from SEC
- ✅ Track multiple stocks simultaneously

### To Implement
- 📋 Parse Form 4 XML for detailed transaction data
- 📋 Analyze stock performance before/after insider trades
- 📋 Detect patterns in insider trading
- 📋 Generate alerts for significant insider activity
- 📋 Create visualizations (price + insider transactions)

## Data Sources

1. **yfinance** - Stock market data
   - Historical prices
   - Company fundamentals
   - Real-time quotes

2. **SEC EDGAR** - Insider trading filings
   - Form 4: Statement of Changes in Beneficial Ownership
   - Filed within 2 business days of transaction
   - Includes purchases, sales, exercises, gifts

## Key SEC Forms

- **Form 3**: Initial Statement of Beneficial Ownership
- **Form 4**: Statement of Changes in Beneficial Ownership (main form for transactions)
- **Form 5**: Annual Statement of Beneficial Ownership

## SEC API Rate Limits

- Maximum 10 requests per second
- Must include valid User-Agent header
- Be respectful to SEC servers

## Next Steps

1. **Parse Form 4 XML**: Extract detailed transaction data (buyer, shares, price, etc.)
2. **Database Integration**: Store historical insider trading data
3. **Analysis Engine**: Identify patterns and correlations
4. **Visualization**: Create charts showing insider trades vs. stock price
5. **Alerts**: Notify when insiders make significant trades

## Resources

- [SEC EDGAR API Documentation](https://www.sec.gov/edgar/sec-api-documentation)
- [yfinance Documentation](https://pypi.org/project/yfinance/)
- [Form 4 Information](https://www.sec.gov/files/forms-3-4-5.pdf)

## Legal Disclaimer

This tool is for educational and research purposes only. Insider trading data is public information, but:
- Always verify data from official sources
- This is not investment advice
- Follow all applicable securities laws
- Be aware that insider trades don't always indicate future performance

## License

MIT License
