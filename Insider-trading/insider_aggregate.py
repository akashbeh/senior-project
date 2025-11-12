import pandas as pd
from pandas import *
from edgar import *

set_identity("sgunawa7@lion.lmu.edu")
filings =  get_filings(form="4", filing_date='2025-11-09:2025-11-11')
exclude_cols = ['Exercise Count', 'Exercise Shares', 'Derivative_Sale Count', 'Derivative_Sale Shares', 
                'Award Count', 'Award Shares', 'Gift Count', 'Gift Shares', 'Derivative_Purchase Count', 
                'Derivative_Purchase Shares', 'Other_Acquisition Count', 'Other_Acquisition Shares', 'Other_Disposition Count', 
                'Other_Disposition Shares','Tax Count', 'Tax Shares']  
transactions = pd.concat([
    f.obj()
     .to_dataframe(detailed=False)
     .drop(columns=exclude_cols, errors='ignore')
    for f in filings
])
transactions.to_csv("transactions_aggregate.csv", index=False)