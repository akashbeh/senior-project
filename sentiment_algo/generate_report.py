import pandas as pd
import numpy as np
import os
from datetime import date, timedelta
from fpdf import FPDF
import ollama 
import matplotlib.pyplot as plt
import io 

# --- Configuration ---
SIGNALS_FILE_PATH = f"/daily_signals/{date.today().strftime('%y-%m-%d')}_signals.csv"
WEEKLY_SUMMARY_DIR = "weekly-summaries"
HISTORICAL_PDF_FILE = "historical-weekly-change.pdf"

# --- Create output directories ---
os.makedirs(WEEKLY_SUMMARY_DIR, exist_ok=True)

# --- Main Functions ---
def generate_weekly_summary(df):
    """Generates a weekly summary based on the Goyal et al. (BERTweet) paper's metrics."""
    print("--- Generating Weekly Summary PDF ---")
    
    today = pd.to_datetime(date.today())
    seven_days_ago = today - timedelta(days=7)
    weekly_df = df[df['timestamp'] >= seven_days_ago].copy()
    
    if weekly_df.empty:
        print("No data found for the last 7 days. Skipping weekly summary.")
        return

    # Aggregate Net SVC and find the Peak Daily SVC for the week
    summary = weekly_df.groupby('ticker').agg(
        net_svc_change_last_7_days=('svc', 'sum'),
        peak_daily_svc=('svc', lambda x: x.abs().max()) # The single largest |SVC| value
    ).reset_index()
    
    significant_changes = summary[summary['net_svc_change_last_7_days'] != 0].copy()
    
    if significant_changes.empty:
        print("No significant changes found this week. Skipping summary.")
        return
        
    # Sort by the most significant single-day event
    significant_changes = significant_changes.sort_values(by='peak_daily_svc', ascending=False)

    # --- PDF Generation ---
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", 'B', 16)
    start_date_str = seven_days_ago.strftime('%Y-%m-%d')
    end_date_str = today.strftime('%Y-%m-%d')
    pdf.cell(0, 10, txt="Weekly Sentiment Summary", ln=True, align='C') #type: ignore
    pdf.set_font("Arial", size=12)
    pdf.cell(0, 10, txt=f"({start_date_str} to {end_date_str})", ln=True, align='C') # type: ignore
    pdf.ln(10)
    
    pdf.set_font("Arial", 'B', 10)
    col_width = pdf.w / 3.5 # Adjusted for 3 columns
    pdf.cell(col_width, 10, 'Stock Ticker', 1, 0, 'C')
    pdf.cell(col_width, 10, 'Net SVC Change', 1, 0, 'C')
    pdf.cell(col_width, 10, 'Peak Daily SVC', 1, 1, 'C')
    
    pdf.set_font("Arial", size=10)
    for _, row in significant_changes.iterrows():
        pdf.cell(col_width, 10, row['ticker'], 1, 0, 'C')
        pdf.cell(col_width, 10, f"{row['net_svc_change_last_7_days']:.2f}", 1, 0, 'C')
        pdf.cell(col_width, 10, f"{row['peak_daily_svc']:.2f}", 1, 1, 'C')
        
    pdf_filename = f"weekly-summary_{start_date_str}_to_{end_date_str}.pdf"
    pdf_path = os.path.join(WEEKLY_SUMMARY_DIR, pdf_filename)
    pdf.output(pdf_path)
    print(f"✅ Weekly summary saved to: {pdf_path}")


def generate_historical_report(df):
    """Generates an overwritten PDF report using the SVC metric from the paper."""
    print("\n--- Generating Overwritten Historical Report PDF ---")
    
    df_weekly = df.groupby('ticker').resample('W-Mon', on='timestamp')['svc'].sum().reset_index()
    df_weekly = df_weekly.rename(columns={'svc': 'weekly_net_svc_change'})
    df_weekly = df_weekly[df_weekly['weekly_net_svc_change'] != 0].copy()
    
    if df_weekly.empty:
        print("No historical data with changes. Skipping historical report.")
        return
        
    df_weekly['week_ending'] = df_weekly['timestamp'].dt.date
    
    # Identify top/bottom 5 stocks from the most recent week based on Net SVC
    most_recent_week = df_weekly['week_ending'].max()
    recent_week_data = df_weekly[df_weekly['week_ending'] == most_recent_week].sort_values('weekly_net_svc_change', ascending=False)
    top_5_positive = recent_week_data.head(5)['ticker'].tolist()
    top_5_negative = recent_week_data.tail(5)['ticker'].tolist()
    
    # --- Helper function to create a plot ---
    def create_plot(tickers, title):
        week_counts = df_weekly['ticker'].value_counts()
        plottable_tickers = [t for t in tickers if week_counts.get(t, 0) >= 2]
        
        if not plottable_tickers: return None

        fig, ax = plt.subplots(figsize=(10, 6))
        for ticker in plottable_tickers:
            ticker_data = df_weekly[df_weekly['ticker'] == ticker].sort_values('week_ending')
            ax.plot(ticker_data['week_ending'], ticker_data['weekly_net_svc_change'], marker='o', linestyle='-', label=ticker)
        
        ax.axhline(0, color='grey', linestyle='--')
        ax.set_title(title, fontsize=14)
        ax.set_xlabel('Date (Week Ending)', fontsize=10)
        ax.set_ylabel('Net Weekly SVC', fontsize=10)
        ax.legend(title='Ticker')
        plt.xticks(rotation=45, ha="right"); plt.tight_layout()
        
        buffer = io.BytesIO(); plt.savefig(buffer, format='png'); buffer.seek(0); plt.close()
        return buffer

    positive_plot_buffer = create_plot(top_5_positive, 'Top 5 Stocks (Positive Net SVC Trend)')
    negative_plot_buffer = create_plot(top_5_negative, 'Top 5 Stocks (Negative Net SVC Trend)')
    
    # --- Generate LLM summary ---
    llm_summary = "No data for LLM analysis."
    try:
        print("🤖 Contacting Ollama for analysis...")
        prompt = f"""
        You are a financial data analyst. The "Net Weekly SVC" (Sentiment Volume Change) metric combines both sentiment change and discussion volume change.

        - A high positive SVC is a GOOD sign. It indicates a significant shift towards positive sentiment accompanied by a surge in discussion volume. This suggests growing bullish conviction.
        - A high negative SVC is a BAD sign, indicating a shift to negative sentiment with high discussion volume, suggesting growing bearish conviction.
        - A value near zero means there was no significant change in sentiment or discussion.

        Based on this and the following weekly data, provide a detailed summary.

        Data:
        {df_weekly.to_markdown(index=False)}

        Your summary should:
        1. Give a high-level overview of sentiment trends.
        2. Identify the top 3 stocks with the strongest positive and negative "Net Weekly SVC" in the most RECENT week.
        3. Analyze stocks that show consistent volatility (big swings in SVC week to week).
        """
        response = ollama.chat(model='llama3', messages=[{'role': 'user', 'content': prompt}])
        llm_summary = response['message']['content']
        print("✅ LLM summary generated.")
    except Exception as e:
        llm_summary = f"LLM summary could not be generated. Error: {e}"
        print(f"❌ Error connecting to Ollama: {e}")

    # --- Create the final historical PDF ---
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(0, 10, 'Historical Sentiment Change Report', ln=True, align='C')
    
    if positive_plot_buffer:
        pdf.ln(10)
        pdf.image(positive_plot_buffer, x=10, w=pdf.w - 20, type='PNG')
    if negative_plot_buffer:
        pdf.ln(5)
        pdf.image(negative_plot_buffer, x=10, w=pdf.w - 20, type='PNG')

    pdf.add_page()
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(0, 10, 'AI-Generated Analysis', ln=True, align='L')
    pdf.set_font("Arial", size=10)
    pdf.multi_cell(0, 5, llm_summary)
    
    pdf.add_page()
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(0, 10, 'Complete Weekly Data', ln=True, align='L')
    col_width = pdf.w / 3.5
    pdf.cell(col_width, 8, 'Week Ending', 1, 0, 'C')
    pdf.cell(col_width, 8, 'Ticker', 1, 0, 'C')
    pdf.cell(col_width, 8, 'Net Weekly SVC', 1, 1, 'C')
    
    pdf.set_font("Arial", size=9)
    for _, row in df_weekly.sort_values(by=['week_ending', 'ticker']).iterrows():
        pdf.cell(col_width, 8, str(row['week_ending']), 1, 0, 'C')
        pdf.cell(col_width, 8, row['ticker'], 1, 0, 'C')
        pdf.cell(col_width, 8, f"{row['weekly_net_svc_change']:.2f}", 1, 1, 'C')
        
    pdf.output(HISTORICAL_PDF_FILE)
    print(f"✅ Historical PDF report overwritten at: {HISTORICAL_PDF_FILE}")

# --- Main Execution ---
if __name__ == "__main__":
    try:
        main_df = pd.read_csv(SIGNALS_FILE_PATH, parse_dates=['timestamp'])
        print(f"Successfully loaded {SIGNALS_FILE_PATH}")
    except FileNotFoundError:
        print(f"Error: The main signals file '{SIGNALS_FILE_PATH}' was not found.")
        exit()
        
    generate_weekly_summary(main_df)
    generate_historical_report(main_df)
    print("\nAll reports generated successfully.")