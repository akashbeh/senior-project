import pandas as pd
from pandas import * 
from edgar import *

OUTPUT = 'transactions_by_ticker.csv'

set_identity("sgunawa7@lion.lmu.edu")

filings = get_filings(form="4", filing_date='2025-11-01:')

exclude_cols = [
    'Exercise Count', 'Exercise Shares', 'Derivative_Sale Count', 'Derivative_Sale Shares',
    'Award Count', 'Award Shares', 'Gift Count', 'Gift Shares', 'Derivative_Purchase Count',
    'Derivative_Purchase Shares', 'Other_Acquisition Count', 'Other_Acquisition Shares',
    'Other_Disposition Count', 'Other_Disposition Shares', 'Tax Count', 'Tax Shares'
]

transaction = pd.concat([
    f.obj()
     .to_dataframe()
    for f in filings
], ignore_index=True, sort=False)

# Filter for Purchase and Sale transactions
filtered = transaction[transaction['Transaction Type'].isin(['Purchase', 'Sale'])]
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
summary.to_csv(OUTPUT)



