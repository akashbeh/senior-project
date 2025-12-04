1. **Install dependencies**:
```bash
pip install -r requirements.txt
```
2. **Update User-Agent in `sec_insider_data.py`**:
   - The SEC requires a valid User-Agent header
   - Replace `set_identity(" ")` with your actual name and email

## Usage

insider_aggregate = Find all insider trading that was filed within a certain timeframe
group_by_ticker = Process insider trading data from a given time frame and sort it by company ticker
Insider_company = Find all insider traders for a specific company within 6 months or specified time
Price_correlation = correlates trading activity with price changes.