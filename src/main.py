#!/usr/bin/env python3

import os
import pandas as pd
from functions import *
from rich.prompt import Prompt
from logger_config import logger
from pytickersymbols import PyTickerSymbols

is_index, is_country = False, False
stock_data = PyTickerSymbols()

search_type = Prompt.ask(
    "Select your search type", choices=["Stock", "Country", "Index"],  default="Stock")
if search_type == "Stock":
    name = Prompt.ask("Enter the symbol of the stock", default="DSY.PA")
elif search_type == "Country":
    is_country = True
    countries = stock_data.get_all_countries()
    name = Prompt.ask("Enter the name of the country",
                      choices=countries, default="France")
else:
    is_index = True
    indices = stock_data.get_all_indices()
    name = Prompt.ask("Enter the symbol of the index",
                      choices=indices, default="CAC 40")

logger.info("Process started.")
logger.debug("Fetching stocks data")
if is_index or is_country:
    companies = get_companies_list(
        name, is_index=is_index, is_country=is_country)
else:
    ticker = yf.Ticker(name)
    companies = {
        "names": [ticker.info["longName"]],
        "symbols": [name]
    }

names = companies["names"]
symbols = companies["symbols"]

# Set the number of years used for the average formula
avg_len = 10


# Calculate the relevant kpis (APY, Avg APYs, ROI)
logger.debug("Calculating KPIs")
kpis = calc_kpis(symbols, avg_len=avg_len)

df = pd.DataFrame({
    'Name': names,
    'Symbol': symbols,
    'ROI (%)': kpis["roi"],
    f"Avg ROI (%, {avg_len}y)": kpis["avgRoi"],
    'APY (%)': kpis["apy"],
    f"Avg APY (%, {avg_len}y)": kpis["avgApy"]
})

# Sort values by ROI
df = df.sort_values(
    by=['ROI (%)'],
    ascending=False
)

base_out_dir = "output"

path = os.path.join(base_out_dir, f"{name}.csv")
if not os.path.exists(base_out_dir):
    os.makedirs(base_out_dir)

# Write result to csv file
logger.debug("Writing result to CSV file \"%s\"", path)
df.to_csv(path, index=False)
logger.info("Output written to \"%s\"", path)
logger.info("Process completed successfully.")
