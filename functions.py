from pytickersymbols import PyTickerSymbols
import yfinance as yf
from datetime import date
import pandas as pd

# Returns the yahoo symbols of all companies
# from the specified asset name (country name, or index)
def getCompanies(name, index=False):
    stock_data = PyTickerSymbols()
    if index:
        rawSymbols = list(stock_data.get_stocks_by_index(name))
    else:
        rawSymbols = list(stock_data.get_stocks_by_country(name))
    companies = []
    for company in rawSymbols:
        name = company['name']
        symbols = company['symbols']
        if len(company['symbols']) > 0:
            symbol = symbols[0]['yahoo']
            companies.append((name,symbol))
    return companies

def getDividends(symbols, years=1):
    dividends = []
    for symbol in symbols:
        apy = getAvgApy(symbol, years=years)
        dividends.append(apy) 
    return dividends

"""
Returns the mean of APYs since the previous "years" years
"""
def getAvgApy(symbol, years=5):
    ticker = yf.Ticker(symbol)
    today = date.today()
    avgApy = 0
    for k in range(years):
        # The end day does not seem to be included
        # So we do day + 1
        start = date(today.year - years + k, today.month, today.day)
        end = date(today.year - years + k + 1, today.month, today.day + 1)
        hist = ticker.history(start=start, end=end)
        if 'Dividends' in hist:
            dividends = hist['Dividends'].sum()
        else:
            dividends = None
        avgPrice = hist['Open'].mean()
        if dividends is not None:
            apy = dividends/avgPrice
            avgApy += apy * 100/years
        else:
            avgApy = None
            break

    return avgApy