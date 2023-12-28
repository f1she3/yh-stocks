from pytickersymbols import PyTickerSymbols
import yfinance as yf
from datetime import date

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
"""


def kpi_get_apy(ticker, start=date.today().replace(month=1, day=1), end=date.today()):
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
        # Get a percentage
        apy *= 100

    return apy


"""
ROI (profitability) = end price - start price + dividends / start price
"""


def kpi_get_roi(ticker, start=date.today().replace(month=1, day=1), end=date.today()):
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
        # Get a percentage
        roi *= 100

    return roi


"""
Returns the average value for the KPI function "kpi_func", for the security whose symbol is "symbol",
for the past "years" years
"""


def get_avg_kpi(ticker, years, kpi_func):
    today = date.today()
    avgKpi = 0
    total = years
    for k in range(years):
        start = today.replace(
            year=today.year-years+k,
            month=1,
            # The end day does not seem to be included
            # So we do day + 1
            day=1
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
            break

    return avgKpi
