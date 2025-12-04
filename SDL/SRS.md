# SDL

## SRS
# 1.0 Requirements Specification

## 1.1 Introduction
The **Stock Analysis System (SAS)** is a terminal-based application that predicts short–term stock movements using social media sentiment, historical stock data and insider or politician trading disclosures. The user runs SAS from the command line, provides API keys and configuration parameters and the system performs the complete analysis pipeline and outputs both a structured PDF report and a text summary in the terminal.

At a high level the system:

1. Scrapes and analyzes sentiment from social media platforms (currently Reddit with Twitter planned as a future extension)  
2. Combines sentiment data with historical price data and insider or politician trades  
3. Generates features and applies a Support Vector Machine (SVM) model to classify expected stock movement  
4. Uses a profit maximizing algorithm to convert these classifications into Buy, Sell or Hold actions  
5. Produces a PDF report with charts, tables and recommendations for the user

A high-level diagram of the SAS components and data flow (social media → semantic analyzer → signal generator → SVM model → profit maximizing algorithm → Buy/Sell/Hold output) is provided in the Architecture section of the SDL.

**Document Outline**

- 1.1 Introduction  
- 1.2 CSCI Component Breakdown  
- 1.3 Functional Requirements by CSC  
- 1.4 Performance Requirements by CSC  
- 1.5 Project Environment Requirements  

---

## 1.2 CSCI Component Breakdown

The Computer Software Configuration Item (CSCI) is the **Stock Analysis System (SAS)**. It is decomposed into Computer Software Components (CSCs) and Computer Software Units (CSUs) as follows.

### 1.2.1 Data Collection CSC (DCSC)

- **1.2.1.1 Social Media Ingestion CSU**  
  Collects raw textual data (posts and comments) from configured social media platforms using their APIs.

- **1.2.1.2 Historical Data Ingestion CSU**  
  Fetches historical price data for relevant tickers from a market data provider for a configurable time window.

- **1.2.1.3 Insider Trading Data Ingestion CSU**  
  Imports insider or politician trading disclosures associated with tickers and dates.

- **1.2.1.4 Data Alignment and Preprocessing CSU**  
  Cleans text, removes duplicates, extracts ticker symbols and aligns timestamps across social media, historical and insider data.

---

### 1.2.2 Sentiment and Semantic Analysis CSC (SACSC)

- **1.2.2.1 Semantic Analyzer CSU**  
  Applies NLP models to classify sentiment at the comment or post level.

- **1.2.2.2 Sentiment Aggregator CSU**  
  Aggregates comment-level sentiment into stock-level metrics over defined windows.

- **1.2.2.3 Sentiment Change Calculator CSU**  
  Computes sentiment change over time for each stock and identifies extreme movers.

---

### 1.2.3 Signal Generation and Modeling CSC (SGMCSC)

- **1.2.3.1 Signal Generator CSU**  
  Combines sentiment metrics, price features and insider indicators into feature vectors.

- **1.2.3.2 SVM Training CSU**  
  Trains an SVM classification model on historical feature vectors and labels.

- **1.2.3.3 SVM Inference CSU**  
  Uses the trained SVM to predict stock movement classes on current feature vectors.

---

### 1.2.4 Recommendation Engine CSC (RECSC)

- **1.2.4.1 Profit Maximizing Algorithm CSU**  
  Computes a score or expected return for each stock using SVM outputs and risk measures.

- **1.2.4.2 Buy/Sell/Hold Classifier CSU**  
  Translates scores into Buy, Sell or Hold actions based on configurable thresholds.

---

### 1.2.5 Report Generation CSC (RGCSC)

- **1.2.5.1 Visualization CSU**  
  Creates charts for top predicted gainers and losers and sample sentiment vs price plots.

- **1.2.5.2 Table Generator CSU**  
  Builds tables summarizing the top 100 stocks and Buy/Sell/Hold results.

- **1.2.5.3 PDF Export CSU**  
  Assembles visuals and tables into a PDF report and writes it to disk.

- **1.2.5.4 CLI Summary CSU**  
  Prints a textual summary of results in the terminal.

---

## 1.3 Functional Requirements by CSC

The following subsections describe what the completed system will do. All requirements are written as individually testable “shall” statements and grouped by CSC from section 1.2.

### 1.3.1 Terminal Execution and Configuration (CSCI-level)

- **1.3.1.1** SAS shall be executable entirely from the terminal as a command-line application.  
- **1.3.1.2** SAS shall prompt the user in the terminal for configuration values including at minimum social media sources, subreddit names, historical data start date and output directory.  
- **1.3.1.3** SAS shall support a non-interactive mode in which configuration parameters are provided via a configuration file or command-line flags.  
- **1.3.1.4** SAS shall read all required API keys and credentials from environment variables or configuration files, not from hard-coded literals.

---

### 1.3.2 Data Collection CSC (DCSC)

**Description:**  
DCSC handles all interactions with external data providers and prepares consistent input datasets for later analysis.

- **1.3.2.1** DCSC shall connect to the Reddit API and download posts and comments from specified subreddits over a user-configurable time window.  
- **1.3.2.2** DCSC shall support at least one additional social media source as a pluggable module which may be stubbed or disabled without affecting core functionality.  
- **1.3.2.3** DCSC shall store downloaded social media data in an internal structure suitable for later processing.  
- **1.3.2.4** DCSC shall invoke Historical Data Ingestion CSU to fetch historical daily price data for all tickers detected in social media content over a configurable historical window.  
- **1.3.2.5** DCSC shall invoke Insider Trading Data Ingestion CSU to import insider or politician trading records for the same ticker set.  
- **1.3.2.6** DCSC shall remove duplicate social media items based on unique identifiers or text hashes.  
- **1.3.2.7** DCSC shall normalize text encodings and case for all social media content.  
- **1.3.2.8** DCSC shall extract ticker symbols using a deterministic parsing rule set and an optional whitelist of valid tickers.  
- **1.3.2.9** DCSC shall align social media timestamps to the same daily or weekly index used by the historical price data.  
- **1.3.2.10** DCSC shall align insider trading records with the same ticker and time index as historical price and sentiment data.

---

### 1.3.3 Sentiment and Semantic Analysis CSC (SACSC)

**Description:**  
SACSC transforms raw cleaned text into quantitative sentiment information for each ticker.

- **1.3.3.1** SACSC shall apply the Semantic Analyzer CSU to each social media item and compute a sentiment representation for that item.  
- **1.3.3.2** SACSC shall associate each sentiment result with its original platform, ticker and timestamp.  
- **1.3.3.3** SACSC shall aggregate sentiment results into ticker-level metrics over configurable windows such as 1 day or 7 days.  
- **1.3.3.4** SACSC shall compute sentiment change metrics for each ticker such as difference and percentage change between current and previous window.  
- **1.3.3.5** SACSC shall identify the tickers with the largest positive and largest negative sentiment changes within the analysis period.  
- **1.3.3.6** SACSC shall export aggregated sentiment metrics in a format that can be consumed by the Signal Generator CSU.

---

### 1.3.4 Signal Generation and Modeling CSC (SGMCSC)

**Description:**  
SGMCSC converts sentiment and market data into feature vectors and applies an SVM model to classify expected stock movement.

- **1.3.4.1** SGMCSC shall construct a feature vector for each ticker and time index that includes sentiment metrics, sentiment change metrics, historical return features, volatility indicators and insider trading flags.  
- **1.3.4.2** SGMCSC shall allow enabling or disabling individual feature types via configuration.  
- **1.3.4.3** SVM Training CSU shall split historical feature vectors and labels into training, validation and test sets.  
- **1.3.4.4** SVM Training CSU shall train an SVM model on the training set and evaluate it on validation and test sets, recording evaluation metrics.  
- **1.3.4.5** SVM Training CSU shall persist the trained SVM model to disk in a format that can be reloaded without retraining.  
- **1.3.4.6** SVM Inference CSU shall load the persisted model and apply it to current feature vectors to obtain predicted movement classes for each stock.  
- **1.3.4.7** SVM Inference CSU shall support at least three movement classes: Up, Down and Hold.

---

### 1.3.5 Recommendation Engine CSC (RECSC)

**Description:**  
RECSC converts SVM outputs into actionable trading recommendations.

- **1.3.5.1** RECSC shall compute a numeric score or expected return for each stock based on SVM predictions and confidence values.  
- **1.3.5.2** Profit Maximizing Algorithm CSU shall rank stocks by this score to maximize expected portfolio profit subject to user-defined risk preferences if provided.  
- **1.3.5.3** Buy/Sell/Hold Classifier CSU shall classify a stock as Buy when its expected return exceeds an upper threshold that is configurable.  
- **1.3.5.4** Buy/Sell/Hold Classifier CSU shall classify a stock as Sell when its expected return is below a lower threshold that is configurable.  
- **1.3.5.5** Buy/Sell/Hold Classifier CSU shall classify a stock as Hold when its expected return lies within the configured hold range, with default range \[-3%, 3%].  
- **1.3.5.6** RECSC shall output for each stock the predicted movement class, final action, score and the primary features or signals that contributed to that decision.  
- **1.3.5.7** RECSC shall generate separate sorted lists of Buy candidates and Sell candidates.

---

### 1.3.6 Report Generation CSC (RGCSC)

**Description:**  
RGCSC presents analysis results to the user in PDF and textual form.

- **1.3.6.1** RGCSC shall generate at least one chart of top predicted positive movers and one chart of top predicted negative movers.  
- **1.3.6.2** RGCSC shall generate at least one time–series chart relating sentiment and price for at least one example ticker.  
- **1.3.6.3** RGCSC shall create a table listing the top 100 stocks ranked by recommendation score or expected return.  
- **1.3.6.4** RGCSC shall create a summary table showing the number of Buy, Sell and Hold classifications.  
- **1.3.6.5** PDF Export CSU shall assemble charts and tables into a PDF report that includes an executive summary and method overview section.  
- **1.3.6.6** PDF Export CSU shall save the PDF report in the user-specified output directory.  
- **1.3.6.7** CLI Summary CSU shall print to the terminal the counts of Buy, Sell and Hold recommendations and the file path of the generated PDF report.

---

## 1.4 Performance Requirements by CSC

This section describes how fast and how efficiently the system must operate. Requirements are grouped by the CSCs that primarily impact them.

### 1.4.1 Data Collection CSC Performance

- **1.4.1.1** DCSC shall complete downloading and preprocessing up to 5000 social media posts and associated price and insider data for up to 500 tickers within 60 seconds on reference hardware.  
- **1.4.1.2** DCSC shall implement retry and back-off logic so that temporary API rate limiting does not cause the run to fail unless limits are exceeded for longer than a configurable timeout.

---

### 1.4.2 Sentiment and Semantic Analysis CSC Performance

- **1.4.2.1** SACSC shall compute sentiment for 5000 social media items within 30 seconds on reference hardware.  
- **1.4.2.2** SACSC shall maintain sentiment classification accuracy of at least 80 percent on available labeled sentiment benchmarks where such benchmarks are used.

---

### 1.4.3 Signal Generation and Modeling CSC Performance

- **1.4.3.1** SGMCSC shall be able to train the SVM model on at least 10 years of daily data for 500 tickers without exceeding 4 GB of RAM on reference hardware.  
- **1.4.3.2** SVM Inference CSU shall classify current feature vectors for 500 tickers in less than 10 seconds on reference hardware.  
- **1.4.3.3** On historical test data SGMCSC shall achieve at least 60 percent directional accuracy for Up, Down and Hold predictions.

---

### 1.4.4 Recommendation Engine CSC Performance

- **1.4.4.1** RECSC shall compute scores and Buy/Sell/Hold classifications for 500 tickers in less than 5 seconds on reference hardware.  

---

### 1.4.5 Report Generation CSC Performance

- **1.4.5.1** RGCSC shall generate all required charts, tables and the final PDF report within 30 seconds after recommendation results are available.  

---

## 1.5 Project Environment Requirements

This section lists the software, hardware and other resources needed for development and execution of SAS.

### 1.5.1 Development Environment Requirements

| Category        | Requirement |
|-----------------|------------|
| Language        | Python 3.x |
| Libraries       | PRAW (Reddit API), optional Twitter client, yfinance, NLTK or TextBlob, scikit-learn, Pandas, Matplotlib, ReportLab |
| IDE             | VS Code or equivalent |
| Version Control | Git and GitHub |
| Operating Systems | macOS, Windows or Linux |

### 1.5.2 Execution Environment Requirements

| Category        | Requirement |
|-----------------|------------|
| Operating System | Any OS supporting Python 3.x |
| Interface        | Terminal only (no GUI) |
| Dependencies     | Reddit API key, market data provider credentials, insider or politician trade dataset, Internet connection |
| Hardware         | Minimum 8 GB RAM, 2.0 GHz CPU, 2 GB free disk space |
| Output           | PDF report written to disk and textual summary printed in terminal |
