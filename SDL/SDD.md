# SDL

## SDD

## 6.0 Software Design Description (SDD)

## 6.1 Introduction  
This document presents the **architecture and detailed design** for the software system **Stock Analysis System (SAS)**.  
The SAS project automates the process of collecting, analyzing, and interpreting stock sentiment data from online communities. It scrapes posts from a stock-related subreddit, performs sentiment analysis, generates visual and tabular reports, cross-references findings with historical and political trading data, and outputs stock recommendations in the form of “Buy” or “Sell.”  

This section focuses on the **Architectural Design**, defining the system’s structure, major components, and their interactions.  

---

### 6.1.1 System Objectives  
The primary objectives of the SAS are:  
1. To automate the collection of community-based sentiment data from Reddit’s stock discussion threads.  
2. To analyze stock sentiment trends using an algorithm.  
3. To visualize sentiment change data and generate comprehensive weekly reports in PDF format.  
4. To correlate sentiment data with historical stock performance and political trading records.  
5. To provide a final, interpretable recommendation for each stock based on aggregated metrics.  

The system aims to enhance the accuracy and accessibility of sentiment-driven investment insights for both technical and non-technical users.  

---

### 6.1.2 Hardware, Software, and Human Interfaces  

#### 6.1.2.1 Hardware Interfaces  
- The system shall operate on standard personal computing hardware.  
- Minimum specifications: 8GB RAM, 2.0 GHz processor, 2GB disk space.  
- Output device: Standard display and optional PDF viewer for generated reports.  

#### 6.1.2.2 Software Interfaces  
- **Operating System:** macOS, Windows, or Linux.  
- **Programming Language:** Python 3.x.  
- **External Libraries:**  
  - `PRAW` for Reddit API scraping.  
  - `NLTK` or `TextBlob` for sentiment analysis.  
  - `Pandas` and `Matplotlib` for data processing and visualization.  
  - `ReportLab` for PDF generation.  
- **Data Sources:** Reddit API, public stock market APIs (e.g., Yahoo Finance, Alpha Vantage), and public political trading datasets (future phse).  

#### 6.1.2.3 Human Interfaces  
- **User Interface:** Command-line interface (CLI) or web dashboard (future phase).  
- **User Interaction:**  
  - Specify online community platform, name, and timeframe.  
  - Trigger analysis and report generation.  
  - View or download PDF report.  
- **Output Interface:** PDF file containing graphs, tables, and recommendations.  

---

## 6.2 Architectural Design  

The architectural design defines the **structure and organization** of the SAS software components and how they interact. The architecture is modular, separating data collection, analysis, and output processes to ensure scalability, maintainability, and testability.  

At a high level, the system follows a **five-layer architecture**:  
1. **Data Collection Layer:** Responsible for fetching and preprocessing online data.  
2. **Analysis Layer:** Performs algoruthm-based sentiment scoring and computes changes over time.  
3. **Cross-Referencing Layer:** Correlates sentiment data with market history and political trade data.  
4. **Recommendation Layer:** Generates confidence scores and buy/sell outputs.  
5. **Reporting Layer:** Produces visual and textual summaries in a structured PDF report.  

---

### 6.2.1 Major Software Components  

#### a. Data Collection Component  
- **Description:** Handles Reddit API calls, collects posts/comments, filters duplicates, and preprocesses text.  
- **Inputs:** Subreddit name, post count, time range.  
- **Outputs:** Cleaned and tokenized dataset ready for sentiment analysis.  

#### b. Sentiment Analysis Component  
- **Description:** Computes sentiment polarity for each stock mention using NLP techniques.  
- **Inputs:** Preprocessed text dataset.  
- **Outputs:** Stock-wise sentiment scores and historical sentiment change metrics.  

#### c. Cross-Referencing Component  
- **Description:** Validates sentiment results by comparing them to historical stock performance and identifying political trades.  
- **Inputs:** Sentiment data, stock performance data, political trade records.  
- **Outputs:** Binary flags indicating correlation and political involvement.  

#### d. Recommendation Engine Component  
- **Description:** Aggregates data from all sources to generate a final “Buy” or “Sell” recommendation.  
- **Inputs:** Sentiment, historical, and political indicators.  
- **Outputs:** Final recommendation score and label per stock.  

#### e. Report Generation Component  
- **Description:** Produces graphs (top 5 positive/negative movers), sentiment tables, and a PDF report.  
- **Inputs:** Aggregated analysis results.  
- **Outputs:** PDF report stored locally and viewable by the user.  

---

### 6.2.2 Major Software Interactions  

1. **Data Flow:**  
   - Reddit API → Data Collection → Sentiment Analysis → Cross-Referencing → Recommendation Engine → Report Generator.  
2. **Interaction Description:**  
   - The **Data Collection** component retrieves subreddit data and passes it to the **Sentiment Analysis** module.  
   - The **Sentiment Analysis** results are transmitted to the **Cross-Referencing** component for validation.  
   - Validated data are then fed into the **Recommendation Engine**, which generates a numerical score and binary recommendation.  
   - Finally, the **Report Generation** component compiles all information into a formatted PDF.  
3. **External Interactions:**  
   - Communication with Reddit API via HTTP.  
   - Retrieval of stock data using third-party APIs.  
   - (future pgase) interaction with external datasets for political trade records.  

---

### 6.2.3 Architectural Design Diagrams  

![Architectural diagram](path/to/image.png)

