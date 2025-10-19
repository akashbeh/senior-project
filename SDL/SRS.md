# SDL

## SRS
# 1.0 Requirements Specification

## 1.1 Introduction  
The **Stock Analysis System (SAS)** is designed to automate the collection, analysis, and recommendation process for stock performance based on sentiment data from online communities, historical stock data, and politician disclosures. The system scrapes a selected **stock-related subreddit**, performs **sentiment analysis** on recent posts, and generates a **PDF report** summarizing sentiment trends. The report includes visualizations of historical sentiment changes, a ranked table of top stocks, and cross-references each with historical market and political trading data. The goal is to provide a **recommendation score** indicating whether a stock is a potential buy or sell.  

**Document Outline:**  
- 1.2 CSCI Component Breakdown  
- 1.3 Functional Requirements  
- 1.4 Performance Requirements  
- 1.5 Project Environment Requirements  

---

## 1.2 CSCI Component Breakdown  

**CSCI: Stock Analysis System (SAS)**  

The SAS is composed of the following CSCs:

### 1.2.1 Data Collection CSC (DCSC)
- **1.2.1.1 Subreddit Scraper CSU:** Gathers text posts and comments from a target subreddit on stocks.  
- **1.2.1.2 Preprocessing CSU:**  Cleans and formats scraped data (removes duplicates, filters noise, tokenizes).  

### 1.2.2 Sentiment Analysis CSC  (SACSC)
- **1.2.2.1 Sentiment Algorithm CSU:** Assigns sentiment polarity scores to each stock mentioned.  
- **1.2.2.2 Historical Change Analysis CSU:**  Calculates changes in sentiment over time (e.g., weekly).  

### 1.2.3 Report Generation CSC  (RGCSC)
- **1.2.3.1 Visualization CSU:** Creates graphs of the top 5 positive and negative sentiment changes.  
- **1.2.3.2 Table Generator CSU:** Produces a table of the top 100 stocks by net weekly sentiment score.  
- **1.2.3.3 PDF Export CSU:** Compiles the report with visuals and tables into a downloadable PDF.  

### 1.2.4 Cross-Referencing CSC  (CRCSC)
- **1.2.4.1 Historical Data Algorithm CSU:** Evaluates whether sentiment correlates with positive stock performance.  
- **1.2.4.2 Political Trade Tracker CSU:** Checks whether politicians have recently bought or sold the stock.  

### 1.2.5 Recommendation Engine CSC  (RECSC)
- **1.2.5.1 Scoring CSU:** Combines sentiment, historical, and political data into a composite score.  
- **1.2.5.2 Recommendation CSU:** Outputs a binary “Buy” or “Sell” recommendation for each stock.  

---

## 1.3 Functional Requirements  

### 1.3.1 Data Collection  
- **1.3.1.1** DCSC shall scrape posts and comments from a specified subreddit.  
- **1.3.1.2** DCSC shall filter out non-stock-related posts and duplicates.  
- **1.3.1.3** DCSC shall preprocess text for sentiment analysis (tokenization, lowercasing, noise removal).  

### 1.3.2 Sentiment Analysis  
- **1.3.2.1** SACSC shall perform sentiment analysis on all mentions of stock tickers.  
- **1.3.2.2** SACSS shall compute weekly net sentiment change for each stock.  
- **1.3.2.3** SACSC shall identify the top five positive and negative sentiment movers.  

### 1.3.3 Report Generation  
- **1.3.3.1** RGCSC shall generate two sentiment trend graphs (top five positive and top five negative).  
- **1.3.3.2** RGCSC shall produce a table of the top 100 stocks ranked by sentiment.  
- **1.3.3.3** RGCSC shall export all results to a PDF report.  

### 1.3.4 Cross-Referencing  
- **1.3.4.1** CRCSC shall retrieve historical stock data for each stock analyzed.  
- **1.3.4.2** CRCSC shall determine whether historical data supports the sentiment trend (binary yes/no).  
- **1.3.4.3** CRCSC shall identify if any analyzed stock has been recently bought by a politician.  

### 1.3.5 Recommendation Engine  
- **1.3.5.1** RECSC shall assign each stock an overall confidence score.  
- **1.3.5.2** RECSC shall classify each stock as a “Buy” or “Sell” recommendation.  

---

## 1.4 Performance Requirements  
- **1.4.1** Complete subreddit scraping and analysis within 60 seconds for up to 500 posts (or API limit).  
- **1.4.2** Generate the full PDF report within 30 seconds after analysis completion.  
- **1.4.3** Maintain a sentiment classification accuracy of at least 80%.  

---

## 1.5 Project Environment Requirements  

### 1.5.1 Development Environment  

| Category | Requirement |
|-----------|--------------|
| Language | Python |
| Frameworks | PRAW (Reddit API), NLTK/TextBlob, Matplotlib, Pandas, ReportLab |
| IDE | VS Code|
| Version Control | Git and GitHub |
| OS | macOS / Windows / Linux |

### 1.5.2 Execution Environment  

| Category | Requirement |
|-----------|--------------|
| Operating System | Any OS supporting |
| Dependencies | Reddit API access key, Internet connection |
| Hardware | 8GB RAM minimum |
| Output | PDF report displayed locally and saved to disk |

