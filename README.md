# Stock Analysis System (SAS) User Manual  
Version 1.0  
CMSI 4071  
Fall 2025

---

# 1. Introduction

The Stock Analysis System (SAS) is a command line software that analyzes social media sentiment, historical market data, and insider trading activity to generate Buy, Sell, or Hold recommendations. The system collects social media comments, processes sentiment, aggregates results into financial signals, trains predictive models, evaluates trading strategies, and produces PDF reports. This manual describes installation, configuration, execution, and troubleshooting for users without technical expertise.

---

# 2. System Requirements

## 2.1 Hardware
- Minimum 8 GB RAM  
- 2 GB available disk space  
- Internet connection

## 2.2 Software
- Python 3.10 or later  
- Pip package manager  
- Terminal access  
- Works on macOS, Windows, and Linux

---

# 3. Installation

## 3.1 Download the Software
Obtain the project by cloning or downloading:
git clone <repository-url>
or download the ZIP and extract it.

## 3.2 Navigate to the Project Directory
cd path/to/sas-project

## 3.3 Install Dependencies
pip install -r requirements.txt

## 3.4 Configure Reddit API Credentials
Create or edit the file:  
~/.config/praw/praw.ini  
Add the following content:  
[bot1]  
client_id=YOUR_CLIENT_ID  
client_secret=YOUR_SECRET  
username=YOUR_USERNAME  
password=YOUR_PASSWORD  
user_agent="SAS Sentiment Scraper"

## 3.5 Configure SEC Edgar Identity
In insider scripts replace:  
set_identity("sgunawa7@lion.lmu.edu")  
with:  
set_identity("your@email")

---

# 4. Directory Structure

```
sas-project/
│
├── sentiment_algo/
│ ├── comment_scraper.py
│ ├── sentiment_analyzer.py
│ ├── aggregate_sentiment.py
│ ├── generate_report.py
│ ├── daily_comments/
│ ├── daily_sentiment/
│ ├── daily_signals/
│ └── weekly-summaries/
│
├── download_price_history.py
├── historical_prices.csv
│
├── svm_stock_classifier.py
├── randomForest.py
├── trading_strategies.py
│
├── insider_aggregate.py
├── insider_company.py
├── Price_correlation.py
│
├── requirements.txt
└── README.md


```


---

# 5. Running the Software

SAS is operated through the terminal. Each stage must be executed in order.

---

# 6. SAS Workflow and Features

## 6.1 Step 1: Collect Reddit Comments
python sentiment_algo/comment_scraper.py  
Outputs:  
daily_comments/YY-MM-DD.csv

## 6.2 Step 2: Run Sentiment Analysis
python sentiment_algo/sentiment_analyzer.py  
Outputs:  
daily_sentiment/YY-MM-DD.csv

## 6.3 Step 3: Aggregate Sentiment and Compute SVC
python sentiment_algo/aggregate_sentiment.py  
Outputs:  
daily_signals/YY-MM-DD_signals.csv

## 6.4 Step 4: Download Historical Price Data
python download_price_history.py  
Outputs:  
historical_prices.csv

## 6.5 Step 5: Train the SVM Model
python svm_stock_classifier.py  
Outputs:  
full_merged_data.csv

## 6.6 Step 6: Train the Random Forest Model
python randomForest.py

## 6.7 Step 7: Generate Weekly and Historical PDF Reports
python sentiment_algo/generate_report.py  
Outputs:  
weekly-summaries/  
historical-weekly-change.pdf

---

# 7. Insider Trading Tools

## 7.1 Aggregate Insider Transactions
python insider_aggregate.py  
Outputs:  
transactions_aggregate.csv

## 7.2 Group Insider Transactions by Ticker
python group_by_ticker.py  
Outputs:  
transactions_by_ticker4.csv

## 7.3 List Insiders for a Company
python insider_company.py

## 7.4 Correlate Insider Trades with Price Movement
python Price_correlation.py

---

# 8. Stopping the Software

Windows:
Ctrl + C

macOS and Linux:
Control + C

---

# 9. Uninstallation

Delete the project folder, then optionally run:
pip uninstall -r requirements.txt

---

# 10. Troubleshooting

## Issue: Reddit scraper cannot authenticate
Verify `praw.ini` credentials.

## Issue: SEC modules fail with HTTP errors
Ensure `set_identity` contains a valid name and email.

## Issue: Sentiment analyzer finds no tickers
Run comment scraper first.

## Issue: Model training fails due to no merged data
Ensure sentiment and price files exist for the same date.

## Issue: Reports contain no data
Run the pipeline for several days to accumulate signal history.

---

# 11. Support

For assistance contact any of the reporistory contributors (except @bjohnson05)

---

# 12. Glossary

| Term | Definition |
|------|-------------|
| Sentiment Volume Change (SVC) | Metric combining sentiment change and discussion volume |
| Support Vector Machine (SVM) | Classification model for predicting movement |
| Random Forest | Ensemble classification model |
| Form 4 Filing | SEC document reporting insider trades |
| Ticker | Stock identifier such as NVDA |

---

# 13. Acronyms

| Acronym | Meaning |
|---------|----------|
| SAS | Stock Analysis System |
| API | Application Programming Interface |
| SEC | United States Securities and Exchange Commission |
| SVC | Sentiment Volume Change |
| CSV | Comma Separated Values |
| PDF | Portable Document Format |

