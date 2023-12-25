#!/usr/bin/env python3

import pandas as pd
from functions import *

# True if asset is an index, False if it's a country
index = False
asset = 'Spain'

companies = getCompanies(asset, index=index)
names = []
symbols = []

# Get companies names & symbols
for company in companies:
    name,symbol = company
    names.append(name)
    symbols.append(symbol)

# Get their APY
apys = getDividends(symbols, years=1)
avgApys = getDividends(symbols, years=5)

df = pd.DataFrame({
    'Name': names,
    'Symbol': symbols,
    'APY (1y)': apys,
    'APY (5y)': avgApys
})
df = df.sort_values(by=['APY (1y)'], ascending=False)
if index:
    path = 'data/indices/' + asset + '.csv'
else:
    path = 'data/countries/' + asset + '.csv'
df.to_csv(path)