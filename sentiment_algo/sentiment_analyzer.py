from pysentimiento import create_analyzer
import pandas as pd
from datetime import date
import os

# --- Define input and output directories ---
input_dir = "daily_comments"
output_dir = "daily_sentiment"
os.makedirs(output_dir, exist_ok=True) # Create the output folder if it doesn't exist

# --- Determine today's file paths ---
today_str = date.today().strftime('%y-%m-%d')
input_file = os.path.join(input_dir, f"{today_str}.csv")
output_file = os.path.join(output_dir, f"{today_str}.csv")

# --- Load Data for Today ---
try:
    df = pd.read_csv(input_file)
    print(f"Successfully loaded {len(df)} comment entries from {input_file}")
except FileNotFoundError:
    print(f"Error: Today's comment file '{input_file}' not found. Please run the scraper first.")
    exit()

# --- Analyzer Setup ---
print("Setting up the sentiment analyzer...")
analyzer = create_analyzer(task="sentiment", lang="en")
print("Analyzer is ready.")

# --- Sentiment Calculation Function ---
def calculate_sentiment_score(comment_text):
    if not isinstance(comment_text, str) or not comment_text.strip():
        return 0.0
    result = analyzer.predict(comment_text)
    pos_score = result.probas['POS']
    neu_score = result.probas['NEU']
    sentiment_score = (pos_score + 0.5 * neu_score) - 0.5
    return sentiment_score

# --- Process and Save ---
print(f"\n🤔 Calculating sentiment for comments from {today_str}...")
df['sentiment_score'] = df['comment_body'].apply(calculate_sentiment_score)
print("✅ Sentiment calculation complete.")

df.to_csv(output_file, index=False)
print(f"\n💾 Data with sentiment scores saved to: {output_file}")