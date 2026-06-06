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
        symbols = company.get('symbols', [])
        if len(symbols) > 0:
            # Get the company's symbol on Yahoo Finance
            symbol = symbols[0]['yahoo']
            companies["names"].append(name)
            companies["symbols"].append(symbol)
    return companies


def _compute_roi_apy(sym_df):
    """Return (roi%, apy%) from a single-ticker OHLCV+Dividends DataFrame."""
    if sym_df is None or sym_df.empty:
        return None, None
    dividends = sym_df['Dividends'].sum() if 'Dividends' in sym_df.columns else 0
    start_price = sym_df.iloc[0]['Open']
    if start_price == 0:
        return None, None
    end_price = sym_df.iloc[-1]['Open']
    roi = (end_price - start_price + dividends) / start_price * 100
    apy = dividends / start_price * 100
    return roi, apy


"""
Returns the relevant Key Performance Indicators (KPI)
of the securities defined in "symbols"
(APY, Avg APY, ROI)

Uses yf.download() to batch-fetch all symbols per date range, reducing
API calls from O(symbols * avg_len) to O(avg_len).
"""


def calc_kpis(symbols, avg_len):
    today = date.today()

    # Range 0: current year. Ranges 1..avg_len: historical years for the avg.
    current_start = today.replace(year=today.year - 1, month=12, day=31)
    ranges = [(current_start, today)]
    for k in range(avg_len):
        start = today.replace(year=today.year - avg_len + k, month=12, day=31)
        end = start.replace(year=start.year + 1)
        if end > today:
            end = today
        ranges.append((start, end))

    per_range = [{} for _ in range(len(ranges))]

    for i, (start, end) in enumerate(ranges):
        batch = yf.download(
            tickers=symbols,
            start=start,
            end=end,
            actions=True,
            progress=False,
            group_by='ticker',
        )
        if batch.empty:
            continue
        for symbol in symbols:
            try:
                sym_df = batch[symbol]
            except KeyError:
                continue
            per_range[i][symbol] = _compute_roi_apy(sym_df)

    result = {"roi": [], "avgRoi": [], "apy": [], "avgApy": []}
    for symbol in symbols:
        roi, apy = per_range[0].get(symbol, (None, None))

        hist_rois = [per_range[i].get(symbol, (None, None))[0] for i in range(1, avg_len + 1)]
        hist_apys = [per_range[i].get(symbol, (None, None))[1] for i in range(1, avg_len + 1)]
        valid_rois = [v for v in hist_rois if v is not None]
        valid_apys = [v for v in hist_apys if v is not None]

        result["roi"].append(roi)
        result["avgRoi"].append(sum(valid_rois) / len(valid_rois) if valid_rois else None)
        result["apy"].append(apy)
        result["avgApy"].append(sum(valid_apys) / len(valid_apys) if valid_apys else None)

    return result
