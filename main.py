#!/usr/bin/env python3

import pandas as pd
from functions import *

index = False
asset = 'Bulgaria'

companies = getCompanies(asset, index=index)
names = []
symbols = []

# Get companies names & symbols
for company in companies:
    name,symbol = company
    names.append(name)
    symbols.append(symbol)
# Get their APY
dividends = getDividends(symbols)

df = pd.DataFrame({
    'Name': names,
    'Symbol': symbols,
    'APY %': dividends
})
df = df.sort_values(by=['APY %'], ascending=False)
if index:
    path = 'data/indices/' + asset + '.csv'
else:
    path = 'data/countries/' + asset + '.csv'
df.to_csv(path)
