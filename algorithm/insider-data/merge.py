import pandas as pd
import os

DIR = os.path.dirname(__file__)
FILE1 = os.path.join(DIR, '2020_01-06.csv')
FILE2 = os.path.join(DIR, '2020_07-12.csv')
df1 = pd.read_csv(FILE1)
df2 = pd.read_csv(FILE2)
merged = pd.concat([df1, df2], ignore_index=True)
merged.to_csv('2020.csv',index=False)
