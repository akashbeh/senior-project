import pandas as pd
from pandas import * 
from edgar import *
from identity import IDENTITY

OUTPUT = 'transactions_by_ticker4.csv'
# A start date of at least 3 days before the end date is recommended,
# because filing is required within about 3 days
START_DATE = '2025-07-01'
END_DATE = '2025-11-29'

set_identity(IDENTITY)

filings = get_filings(form="4", filing_date=f'{START_DATE}:{END_DATE}')

dataframes = []
for f in filings:
    try:
        obj = f.obj()
        if obj is not None:
            df = obj.to_dataframe()
            dataframes.append(df)
    except (AttributeError, KeyError, Exception) as e:
        print(f"Skipping filing {f.accession_no} due to parsing error: {type(e).__name__}")
        continue

transaction = pd.concat(dataframes, ignore_index=True, sort=False) if dataframes else pd.DataFrame()

# Filter for Purchase and Sale transactions
filtered = transaction[transaction['Transaction Type'].isin(['Purchase', 'Sale'])]
filtered.to_csv("TransactionsByDate.csv", index=False)

# Group by Ticker
grouped = filtered.groupby('Ticker')

def compute_metrics(df):
    total_sale_transactions = len(df[df['Transaction Type'] == 'Sale'])
    total_purchase_transactions = len(df[df['Transaction Type'] == 'Purchase'])
    sales_value = df[df['Transaction Type'] == 'Sale']['Value'].sum()
    purchases_value = df[df['Transaction Type'] == 'Purchase']['Value'].sum()
    sales_share = df[df['Transaction Type'] == 'Sale']['Shares'].sum()
    purchases_share = df[df['Transaction Type'] == 'Purchase']['Shares'].sum()
    buy_sell_ratio = total_purchase_transactions / total_sale_transactions if total_sale_transactions != 0 else 0
    return pd.Series({
        'Total Sale Transactions': total_sale_transactions,
        'Total Purchase Transactions': total_purchase_transactions,
        'Total Sales Value': sales_value,
        'Total Purchases Value': purchases_value,
        'Total Sales Shares': sales_share,
        'Total Purchases Shares': purchases_share,
        'Buy/Sell Ratio': buy_sell_ratio
    })

summary = grouped.apply(compute_metrics, include_groups=False)
summary.to_csv("TransactionsByTicker.csv")
