from pytickersymbols import PyTickerSymbols
import yfinance as yf
from datetime import date
from logger_config import logger

"""
Returns the yahoo symbols of all the companies
belonging to the specified index or country
"""


def get_companies_list(name="France", is_index=False, is_country=True):
    stock_data = PyTickerSymbols()
    if is_country:
        raw_symbols = list(stock_data.get_stocks_by_country(name))
    elif is_index:
        raw_symbols = list(stock_data.get_stocks_by_index(name))
    else:
        raise Exception(
            "get_companies_list() : The symbol must either be an index or a country.")
    companies = {
        "names": [],
        "symbols": []
    }
    for company in raw_symbols:
        name = company['name']
        symbols = company['symbols']
        if len(company['symbols']) > 0:
            # Get the company's symbol on Yahoo Finance
            symbol = symbols[0]['yahoo']
            companies["names"].append(name)
            companies["symbols"].append(symbol)
    return companies


"""
Returns the relevant Key Performance Indicators (KPI)
of the securities defined in "symbols"
(APY, Avg APY, ROI)
"""


def calc_kpis(symbols, avg_len):
    result = {
        "roi": [],
        "avgRoi": [],
        "apy": [],
        "avgApy": [],
    }
    for symbol in symbols:
        ticker = yf.Ticker(symbol)

        roi = kpi_get_roi(ticker)
        avg_roi = get_avg_kpi(ticker, years=avg_len, kpi_func=kpi_get_roi)
        apy = kpi_get_apy(ticker)
        avg_apy = get_avg_kpi(ticker, years=avg_len, kpi_func=kpi_get_apy)

        result["roi"].append(roi)
        result["avgRoi"].append(avg_roi)
        result["apy"].append(apy)
        result["avgApy"].append(avg_apy)
    return result


"""
APY (yield) = dividends / start price

Calculated 
    from December 31st, previous year 
    (
        to December 31st, this year
        or 
        to today's date
    )
"""


def kpi_get_apy(
    ticker,
    # yfinance: Start date included
    start=date.today().replace(year=date.today().year - 1, month=12, day=31),
    # yfinance: End date excluded
    end=date.today()
):
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
            logger.warning(f"Error while calculating the APY for {tickerName}")
        else:
            apy = dividends / start_price
        # Get a percentage
        apy *= 100

    return apy


"""
ROI (profitability) = end price - start price + dividends / start price

Calculated 
    from December 31st, previous year (included)
    (
        to December 31st, this year (included)
        or 
        to today (excluded)
    )
"""


def kpi_get_roi(
    ticker,
    # yfinance: Start date included
    start=date.today().replace(year=date.today().year - 1, month=12, day=31),
    # yfinance: End date excluded
    end=date.today()
):
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
            logger.warning(f"Error while calculating the ROI for {tickerName}")
        else:
            roi = (end_price - start_price + dividends) / start_price
        # Get a percentage
        roi *= 100
    return roi


"""
Returns the average value for the KPI function "kpi_func", for the security whose symbol is "symbol",
for the past "years" years

I chose a year to be
    from December 31st, previous year
    to
    (
        December 31st, next year
        or
        today if (December 31st, next year) > today
    )

This is the most realiable way I found to have consistent data from yfinance.
For some reason, if "2000-01-01" is used as "start", 
the first value returned is "2000-01-02", a day later.
With "1999-12-31", the first value corresponds indeed to "1999-12-31"
"""


def get_avg_kpi(ticker, years, kpi_func):
    today = date.today()
    avgKpi = 0
    total = years
    for k in range(years):
        start = today.replace(
            year=today.year-years+k,
            month=12,
            day=31
        )
        end = start.replace(year=start.year+1)
        # The end date can't be in the future
        if (end > date.today()):
            end = date.today()
        kpi = kpi_func(ticker=ticker, start=start, end=end)
        # Skip the value if the execution went wrong
        if kpi == None:
            total -= 1
            continue
        else:
            avgKpi += kpi/total

    return avgKpi
