from pytickersymbols import PyTickerSymbols
import yfinance as yf

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

def getDividends(symbols):
    dividends = []
    for symbol in symbols:
        apy = getApy(symbol)
        dividends.append(apy) 
    return dividends
def getApy(symbol):
    ticker = yf.Ticker(symbol)
    hist = ticker.history(period="1y")
    avgPrice = hist['Open'].mean()
    if 'Dividends' in hist:
        dividends = hist['Dividends'].sum()
    else:
        dividends = None
    if dividends is not None:
        if dividends > 0:
            # APY (%)
            apy = dividends / avgPrice * 100
        else:
            apy = 0
    else:
        apy = None
    """
    key = 'trailingAnnualDividendYield'
    if(key in ticker.info):
        tady = ticker.info['trailingAnnualDividendYield']
        if tady is not None:
            tady = tady * 100
    else:
        tady = None
    """

    return apy