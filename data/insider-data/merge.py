import pandas as pd
import os

DATA1 = '2020_01-06.csv'
DATA2 = '2020_07-12.csv'
OUTPUT = '2020.csv'

DIR = os.path.dirname(__file__)
FILE1 = os.path.join(DIR, DATA1)
FILE2 = os.path.join(DIR, DATA2)
df1 = pd.read_csv(FILE1)
df2 = pd.read_csv(FILE2)
merged = pd.concat([df1, df2], ignore_index=True)
merged.to_csv(OUTPUT,index=False)
