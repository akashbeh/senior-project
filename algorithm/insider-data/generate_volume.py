import pandas as pd
import os

DIR = os.path.dirname(__file__)
FILE = os.path.join(DIR, '2020-clean.csv')
DEST = os.path.join(DIR, '2020-full.csv')
df = pd.read_csv(FILE)

# 1) Read as strings to avoid unwanted auto-conversion
df = pd.read_csv("trades.csv", dtype=str)

# 2) Trim whitespace on all object columns (common source of "different" rows)
for c in df.select_dtypes(include=["object"]).columns:
    df[c] = df[c].str.strip()

# 3) Normalize column names (optional but helps)
df.columns = [c.strip() for c in df.columns]

# 4) Parse/clean Date, Shares, Value carefully

# Date -> pandas.Timestamp (normalized to date only for grouping)
df['Date'] = pd.to_datetime(df['Date'], errors='coerce')  # NaT where parse fails
df['Date_only'] = df['Date'].dt.normalize()  # midnight timestamps; or use .dt.date if you prefer

# Shares -> integer (nullable Int64) — remove commas, coerce bad values to NaN
df['Shares'] = pd.to_numeric(df['Shares'].str.replace(',', ''), errors='coerce').astype('Int64')

# Value -> numeric (float) but we'll also create an integer-cents column to normalize tiny float differences
# Remove currency symbols and thousands separators first (adjust regex if your data differs)
df['Value'] = pd.to_numeric(df['Value'].str.replace(r'[\$,]', '', regex=True), errors='coerce')

# create a cents integer column (rounding to nearest cent) to use when detecting exact duplicates
df['Value_cents'] = (df['Value'] * 100).round().astype('Int64')

# If 'Remaining Shares' should be integer:
if 'Remaining Shares' in df.columns:
    df['Remaining Shares'] = pd.to_numeric(df['Remaining Shares'].str.replace(',', ''), errors='coerce').astype('Int64')

# 5) Build the subset for deduplication using normalized fields
# Use Value_cents instead of Value to avoid floating point tiny-differences
subset = ["Code", "Shares", "Value_cents", "Date_only", "Ticker"]

# If any of these columns might be missing, adjust subset accordingly:
subset = [c for c in subset if c in df.columns]

# 6) Drop duplicates (keep first occurrence)
before = len(df)
df = df.drop_duplicates(subset=subset, keep='first')
after = len(df)
print(f"Dropped {before-after} duplicates (based on {subset})")

# 7) Now compute per-row absolute-dollar volume and group by Ticker + Date
# Ensure Value is numeric (already handled above). If some Values are NaN, decide how you want to treat them.
df['RowVolume'] = df['Value'].abs()

# Group and aggregate. Adjust aggregations for other columns (e.g., Remaining Shares -> last)
grouped = (
    df
    .groupby(['Ticker', 'Date_only'], as_index=False)
    .agg({
        'Shares': 'sum',             # total shares
        'Value': 'sum',              # signed net value
        'RowVolume': 'sum',          # sum of abs values -> this is the Volume you wanted
        'Remaining Shares': 'last',  # example: keep last remaining shares (change if needed)
        'Code': lambda s: ','.join(s.dropna().unique())  # join unique Codes if you want a summary
    })
    .rename(columns={'RowVolume': 'Volume', 'Date_only': 'Date'})
)

# If you want Date as a date (not Timestamp):
grouped['Date'] = pd.to_datetime(grouped['Date']).dt.date

print(grouped.head())

