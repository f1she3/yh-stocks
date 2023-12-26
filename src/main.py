#!/usr/bin/env python3

import os
import pandas as pd
from functions import *

# True if asset is an index, False if it's a country
index = False
asset = 'France'

companies = get_companies(asset, index=index)
names = []
symbols = []

# Get companies names & symbols
for company in companies:
    name, symbol = company
    names.append(name)
    symbols.append(symbol)

# Set the number of years used for the average formula
avg_len = 8

# Calculate the relevant kpis (APY, Avg APYs, ROI)
kpis = calc_kpis(symbols, avg_len=avg_len)

df = pd.DataFrame({
    'Name': names,
    'Symbol': symbols,
    'ROI (%)': kpis["roi"],
    f"Avg ROI (%, {avg_len}y)": kpis["avgRoi"],
    'APY (%)': kpis["apy"],
    f"Avg APY (%, {avg_len}y)": kpis["avgApy"]
})
df = df.sort_values(
    by=['ROI (%)'],
    ascending=False
)

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

df.to_csv(path, index=False)
