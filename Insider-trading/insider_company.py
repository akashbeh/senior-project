import pandas as pd
from rich import print
from tqdm.auto import tqdm

from edgar import *
from edgar.entity import EntityFilings
from edgar.ownership import Form4
from datetime import datetime, timedelta


# Calculate the date 6 months ago from today

date_range = ((datetime.now() - timedelta(days=6*30)) # Approximate 6 months
              .strftime('%Y-%m-%d:'))

set_identity("sgunawa7@lion.lmu.edu")

def get_insiders(ticker):
    c: Company = Company(ticker)
    filings: EntityFilings = c.get_filings(form='4', filing_date=date_range)

    dfs = []

    for filing in tqdm(filings):
        form4: Form4 = filing.obj()
        summary = form4.get_ownership_summary()
        dfs.append(summary.to_dataframe()[['Insider', 'Position']])
        

    insiders = (pd.concat(dfs, ignore_index=True)
                 .drop_duplicates().reset_index(drop=True)
                 .sort_values(by='Position', key=lambda col: col == 'Director', ascending=True)
                 )
    return insiders

if __name__ == '__main__':
    insiders = get_insiders("NFLX")
    print(insiders)