import pandas as pd
import os

DIR = os.path.dirname(__file__)
FILE = os.path.join(DIR, '2020.csv')
df = pd.read_csv(FILE)

# Deduplicate
df.drop_duplicates(subset=None, keep="first", inplace=True)

# Capitalize the ticker
df["Ticker"] = df["Ticker"].str.replace(r'[^A-Za-z]', '', regex=True).str.upper()

# Check that every code is s or p
valid = {"S", "P"}
assert set(df["Code"]).issubset(valid), "Invalid Code values found"

# Set value and shares to negative if code is "sell"
df['Code'] = df['Code'].str.strip().str.lower()
df.loc[df['Code'] == 's', 'Value'] *= -1
df.loc[df['Code'] == 's', 'Shares'] *= -1

# Compute volume per row
df["Volume"] = df["Value"].abs()

# Compute remaining value
df["Remaining Shares"] = pd.to_numeric(df["Remaining Shares"], errors="coerce")
df["Remaining"] = df["Remaining Shares"] * df["Price"]

df = (
    df
    .groupby(["Ticker", "Date", "Insider"], as_index=False)
    .agg({
        "Value": "sum",
        "Volume": "sum",
        "Remaining": "last"
    })
)

# Clean up date
df["Date"]  = pd.to_datetime(df["Date"], format="mixed")
df = df.sort_values(['Ticker', 'Date'])


# COMPUTE SUMS
times = {"Week": "7d", "Month": "30d", "TriMonth": "91d"}
for section in ["Value", "Volume", "Remaining"]:
    df = df.set_index('Date')
    # Compute rolling sum per Ticker
    for time, days in times.items():
        df[f'{time}ly {section}'] = (
            df.groupby('Ticker')[section]
              .rolling(days).sum()
              .reset_index(level=0, drop=True)
        )
    # Reset index to keep Date as a column
    df = df.reset_index()

# Aggregate across buyers
df = (
    df
    .groupby(["Ticker", "Date"], as_index=False)
    .agg({
        "Value": "sum",
        "Volume": "sum",
        "Remaining": "sum",
        "Weekly Value": "sum",
        "Weekly Volume": "sum",
        "Weekly Remaining": "sum",
        "Monthly Value": "sum",
        "Monthly Volume": "sum",
        "Monthly Remaining": "sum",
        "TriMonthly Value": "sum",
        "TriMonthly Volume": "sum",
        "TriMonthly Remaining": "sum",
    })
)


# Compute features

df["Buyer Change Day"] = df["Remaining"] / df["Value"]
df["Trade Direction Day"] = df["Value"] / df["Volume"]
for time in times:
    df[f"Buyer Change {time}"] = df[f"{time}ly Remaining"] / df[f"{time}ly Value"]
    df[f"Trade Direction {time}"] = df[f"{time}ly Value"] / df[f"{time}ly Volume"]



df = df[[
    "Ticker", 
    "Date", 
    "Buyer Change Day", 
    "Buyer Change Week", 
    "Buyer Change Month", 
    "Buyer Change TriMonth", 
    "Trade Direction Day", 
    "Trade Direction Week", 
    "Trade Direction Month", 
    "Trade Direction TriMonth"
]]

df.to_csv('2020-clean.csv',index=False)
