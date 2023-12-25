#!/usr/bin/env python3

import os
import pandas as pd
from functions import *

# True if asset is an index, False if it's a country
index = False
asset = 'France'

companies = getCompanies(asset, index=index)
names = []
symbols = []

# Get companies names & symbols
for company in companies:
    name, symbol = company
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

base_out_dir = "output"
final_dir = ""

if index:
    final_dir = "indices"
else:
    final_dir = "countries"

out_dir = os.path.join(base_out_dir, final_dir)

path = os.path.join(out_dir, f"{asset}.csv")
if not os.path.exists(out_dir):
    os.makedirs(out_dir)

df.to_csv(path)
