# Stock Analysis System (SAS) User Manual  
Version 1.0  
CMSI 4071  
Fall 2025

---

# 1. Introduction

Stock Analysis System (SAS) is a command line software that analyzes social media sentiment, historical market data, and insider trading activity to generate Buy, Sell, or Hold recommendations. The system collects social media comments, processes sentiment, aggregates results into financial signals, trains predictive models, evaluates trading strategies, and produces PDF reports. This manual describes installation, configuration, execution, and troubleshooting for users without technical expertise.

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
```
git clone <repository-url>
```
or download the ZIP and extract it.

## 3.2 Navigate to the Program Directory
```
cd senior-project/program
```

## 3.3 Install Dependencies
Install dependencies with this command:

```
pip install -r requirements.txt
```

---

# 4. Configuration
Some of this configuration may not be necessary depending on later steps.

## 4.1 SEC Edgar Identity
In Insider-trading/identity.py change IDENTITY to your own email. 

## 4.2 Configure Reddit API Credentials
Create or edit the file:  
```
~/.config/praw/praw.ini  
```
Add the following content:  
```
[bot1]  
client_id=YOUR_CLIENT_ID  
client_secret=YOUR_SECRET  
username=YOUR_USERNAME  
password=YOUR_PASSWORD  
user_agent="SAS Sentiment Scraper"
```

## 4.3 Configure Twitter API
```
cd sentiment_algo
```
Edit scrape_twitter.py:
```
API_KEY = "your API key"
```
Return
```
cd ..
```

---

# 5. Collect data
An existing Random Forest model has been trained and saved. In order to use it, data must be collected. 

Data collection could also be used to re-train the model over a different time period (ours was 2020).

## 5.1 Historical prices (Directory: historical_prices/)
The fundamental data.

```
cd historical_prices
python3 download_price_history.py
```


## 5.2 Insider Trading

### 5.2.2 Download data
```
cd Insider-trading
```
Edit group_by_ticker.py:
```
START_DATE = "YYYY-MM-DD"
END_DATE = "YYYY-MM-DD"
```
Run script:
```
python3 group_by_ticker.py
```

Start date should be at least 3 days before end date, because insider trading data must be released within about 3 days.

For training in final_algo/rf_full.py, at least 3 months of insider trading data is required. Therefore if start date is not 3 months before, more data should be collected and merged (see below).

### 5.2.3 Move data
```
mv TransactionsByTicker.csv ../data/insider-data/
cd ../data/insider-data/
```

### 5.2.4 (Optional) Merge data
Use data/insider-data/merge.py to merge multiple data sets. Make sure to change the filename constants at the top of the program.

Editing merge.py
```
DATA1 = "yourTransactionsByTicker1.csv"
DATA2 = "yourTransactionsByTicker2.csv"
OUTPUT = "yourMergedFile.csv"
```
Run
```
python3 merge.py
```

### 5.2.5 Clean data
Use data/insider-data/clean.py to refine the data. Change the filenames before running.

Editing clean.py
```
INPUT = "yourMergedFile.csv"
OUTPUT = "cleanData.csv"
```
Run
```
python3 clean.py
```

(The full process is described in data/insider-data/data-refinement.txt.)

### 5.2.6 (Optional) Insider Trading Tools

#### 5.2.6.1 Aggregate Insider Transactions
```
python insider_aggregate.py  
```
Outputs:  
transactions_aggregate.csv

#### 5.2.6.2 List Insiders for a Company
```
python insider_company.py
```

#### 5.2.6.3 Correlate Insider Trades with Price Movement
```
python Price_correlation.py
```


## 5.3 Sentiment Analysis (Directory: sentiment_algo/)
Various sources of data are available here; the analysis will ultimately be saved in signals/. The Reddit API can only download recent data, so for training, you can either scrape present data repeatedly, or use the archive. The archive is optimal for generating consistent sentiment signals, but takes a long time to download and process.

### 5.3.1 (Optimal) Reddit Archive
Reddit archives are available at the-eye.eu . Subreddits such as r/wallstreetbets (our SUBREDDIT_LIST is in scrape_reddit.py) can be downloaded.

Download to data/reddit-archive/. Then run reddit_archive_parser.py .

In case the process is interrupted, it can be resumed by re-running and selecting "y" to loading from the checkpoint file. Otherwise, select "n".

### 5.3.2  Scraping data
Data may be scraped from Reddit and/or Twitter.

#### 5.3.2.1 Scraping Reddit
Requires Configuration 4.2

The Sentiment Pipeline run_pipeline.sh collects Reddit comments for that day and generates corresponding sentiment signals. With a cronjob, it can be set up to run daily.

#### 5.3.2.2 Twitter Scraper
Requires Configuration 4.3

The Twitter Scraper scrape_twitter.py collects a large number of tweets. To use it, insert your API_KEY.

#### 5.3.2.3 Merge data
Now go to data/ and run merge_sentiment_price.py.

#### 5.3.2.4 (Optional) Generate report
If you have run the Sentiment Pipeline consistently, you may generate the weekly summary using generate_report.py.

## 5.4 Finish data
In data/, you should now have merged_data.csv. Run finish_merge.py to get full_full_data.csv.

---

# 6. (Optional) Train model
CAUTION: This will overwrite the existing saved model.

Go to final_algo/. Run rf_full.py.

You can also run rf_no_insider.py if you did not collect the insider trading data. A separate model is saved.

---

# 7. Predict stocks
Data for the past 3 months must be gathered through the above steps to calculate all metrics used as features.

Filter your data through LibreOffice Calc, Microsoft Excel, etc to only include today's data. Then rename your data to present_data.csv and place it in data/. As an example, one of our days of data was taken for present_data.csv.

Run predict.py and you will receive recommendations.

---

# 8. Directory Structure
```
sas_repository/
|
├── ABCDR Presentation/
├── Assignments/
│
├── Instructor Feedback/
├── Poster/
├── Project Proposal/
├── SDL/
├── Status Reports/
│
├── program
│   ├── data
│   │   ├── finish_merge.py
│   │   ├── full_full_data.csv
│   │   ├── insider-data
│   │   │   ├── clean.py
│   │   │   ├── data-refinement.txt
│   │   │   └── merge.py
│   │   ├── merged_data.csv
│   │   ├── merge_sentiment_price.py
│   │   ├── nasdaq_screener.csv
│   │   └── reddit-archive/
│   ├── final_algo
│   │   ├── rf_full.py
│   │   ├── rf_no_insider.py
│   │   └── trading_strategies.py
│   ├── historical_prices
│   │   ├── download_price_history.py
│   │   └── historical_prices.csv
│   ├── Insider-trading
│   │   ├── group_by_ticker.py
│   │   ├── identity.py
│   │   ├── insider_aggregate.py
│   │   ├── insider_company.py
│   │   ├── Price_correlation.py
│   │   ├── README.md
│   └── sentiment_algo
│       └── weekly-summaries/
│       ├── generate_report.py
│       ├── historical-weekly-change.pdf
│       ├── reddit_archive_parser.py
│       ├── requirements.txt
│       ├── run_pipeline.sh
│       ├── scrape_reddit.py
│       ├── scrape_twitter.py
│       ├── sentiment_analyzer.py
│       ├── signal_generator.py
│       ├── svm_stock_classifier.py
|
├── README.md
└── features.txt
```

---

# 9. Running the Software

SAS is operated through the terminal as described above. Each stage must be operated in order.

---

# 10. SAS Performance

SAS trading strategies outperformed Buy and Hold on the testing set with better return (4.0584% vs 3.9581%), less risk (0.1463% vs 0.1516%), and consequently higher Sharpe Ratio (10.2961 vs 9.6909). The full results are in program/final_algo/rf_full_results.txt. 

An example of predictions is in program/final_algo/predict_example.txt. The examples are drawn from the merged_data.csv, full_full_data.csv, and present_data.csv in the repository (program/data/).

---

# 11. Stopping the Software

Windows:
Ctrl + C

macOS and Linux:
Control + C

---

# 12. Uninstallation

Delete the project folder, then optionally run:
pip uninstall -r requirements.txt

---

# 13. Troubleshooting

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

# 14. Support

For assistance contact any of the repository contributors (except @bjohnson05)

---

# 15. Glossary

| Term | Definition |
|------|-------------|
| Sentiment Volume Change (SVC) | Metric combining sentiment change and discussion volume |
| Support Vector Machine (SVM) | Classification model for predicting movement |
| Random Forest | Ensemble classification model |
| Form 4 Filing | SEC document reporting insider trades |
| Ticker | Stock identifier such as NVDA |

---

# 16. Acronyms

| Acronym | Meaning |
|---------|----------|
| SAS | Stock Analysis System |
| API | Application Programming Interface |
| SEC | United States Securities and Exchange Commission |
| SVC | Sentiment Volume Change |
| CSV | Comma Separated Values |
| PDF | Portable Document Format |

