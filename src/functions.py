from pytickersymbols import PyTickerSymbols
import yfinance as yf
from datetime import date

"""
Returns the yahoo symbols of all companies
from the specified asset name (country name, or index)
"""


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
            companies.append((name, symbol))
    return companies


def getDividends(symbols, years=1):
    dividends = []
    for symbol in symbols:
        apy = getAvgApy(symbol, years=years)
        dividends.append(apy)
    return dividends


"""
APY (yield) = dividends / start price
"""


def getApy(ticker, start, end):
    hist = ticker.history(start=start, end=end)
    apy = None
    if not hist.empty:
        if 'Dividends' in hist:
            dividends = hist['Dividends'].sum()
        else:
            dividends = 0
        # The price at the begining of the year (First row of the dataframe)
        start_price = hist.iloc[0]['Open']
        if (start_price == 0):
            tickerName = ticker.get_info["longName"]
            print(f"Error while calculating the APY for {tickerName}")
        else:
            apy = dividends / start_price

    return apy


"""
ROI (profitability) = end price - start price + dividends / start price
"""


def getRoi(ticker, start, end):
    hist = ticker.history(start=start, end=end)
    roi = None
    if not hist.empty:
        if 'Dividends' in hist:
            dividends = hist['Dividends'].sum()
        else:
            dividends = 0
        # The price at the begining of the year (First row of the dataframe)
        start_price = hist.iloc[0]['Open']
        end_price = hist.iloc[-1]['Open']
        if (start_price == 0):
            tickerName = ticker.get_info["longName"]
            print(f"Error while calculating the ROI for {tickerName}")
        else:
            roi = (end_price - start_price + dividends) / start_price

    return roi


"""
Returns the mean of APYs since the previous "years" years
"""


def getAvgApy(symbol, years=5):
    ticker = yf.Ticker(symbol)
    today = date.today()
    avgApy = 0
    total = years
    for k in range(years):
        start = today.replace(
            year=today.year-years+k,
            month=1,
            # The end day does not seem to be included
            # So we do day + 1
            day=2
        )
        end = start.replace(year=start.year+1)
        # The end date can't be in the future
        if (end > date.today()):
            end = date.today()
        apy = getApy(ticker=ticker, start=start, end=end)
        # Skip the value if the execution went wrong
        if apy == None:
            total -= 1
            continue
        else:
            avgApy += apy/total
            break
    # Get a percentage
    avgApy *= 100

    return avgApy
