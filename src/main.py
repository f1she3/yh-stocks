#!/usr/bin/env python3

import argparse
import os
import pandas as pd
from functions import *
from logger_config import logger


# Dynamic arguments
parser = argparse.ArgumentParser(description='Process some variables.')

parser.add_argument('--is_index', type=lambda x: (str(x).lower() == 'true'), default=False,
                    help='True if asset is an index, False if it\'s a country (default: False)')
parser.add_argument('--is_country', type=lambda x: (str(x).lower() == 'true'), default=False,
                    help='True if asset is a country, False otherwise (default: False)')
parser.add_argument('--name', type=str, default='PSP5.PA',
                    help='Name of the asset (default: \'PSP5.PA\')')

args = parser.parse_args()

is_index = args.is_index
is_country = args.is_country
name = args.name

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
logger.debug("Writing result to CSV file")
df.to_csv(path, index=False)
logger.info("Process completed successfully.")
