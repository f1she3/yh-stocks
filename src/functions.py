from datetime import date

import pandas as pd
import yfinance as yf
from pytickersymbols import PyTickerSymbols

from logger_config import logger


def get_companies_list(name: str = "France", is_index: bool = False, is_country: bool = True) -> dict:
    stock_data = PyTickerSymbols()
    if is_country:
        raw_symbols = list(stock_data.get_stocks_by_country(name))
    elif is_index:
        raw_symbols = list(stock_data.get_stocks_by_index(name))
    else:
        raise ValueError("get_companies_list(): must specify is_index or is_country")
    companies: dict = {"names": [], "symbols": []}
    for company in raw_symbols:
        symbols = company.get("symbols", [])
        if symbols:
            companies["names"].append(company["name"])
            companies["symbols"].append(symbols[0]["yahoo"])
    return companies


def _compute_roi_apy(sym_df: pd.DataFrame | None) -> tuple[float | None, float | None]:
    if sym_df is None or sym_df.empty:
        return None, None
    sym_df = sym_df.dropna(subset=["Open"])
    if sym_df.empty:
        return None, None
    dividends = sym_df["Dividends"].sum() if "Dividends" in sym_df.columns else 0.0
    start_price = float(sym_df.iloc[0]["Open"])
    if start_price == 0:
        return None, None
    end_price = float(sym_df.iloc[-1]["Open"])
    roi = (end_price - start_price + dividends) / start_price * 100
    apy = dividends / start_price * 100
    return roi, apy


def _download_batch(
    symbols: list[str],
    start: date,
    end: date,
    timeout: int = 30,
) -> pd.DataFrame:
    try:
        return yf.download(
            tickers=symbols,
            start=start,
            end=end,
            actions=True,
            progress=False,
            group_by="ticker",
            timeout=timeout,
        )
    except Exception as exc:
        logger.warning("yf.download failed for batch: %s", exc)
        return pd.DataFrame()


def calc_kpis(symbols: list[str], avg_len: int = 10, timeout: int = 30) -> dict:
    """
    Returns ROI/APY KPIs for each symbol.

    Keys in the returned dict:
      roi, avgRoi, apy, avgApy      — scalar per symbol (existing contract)
      roiSeries, apySeries          — list[list[float|None]] of per-year values per symbol
    """
    today = date.today()

    current_start = today.replace(year=today.year - 1, month=12, day=31)
    ranges = [(current_start, today)]
    for k in range(avg_len):
        start = today.replace(year=today.year - avg_len + k, month=12, day=31)
        end = start.replace(year=start.year + 1)
        if end > today:
            end = today
        ranges.append((start, end))

    per_range: list[dict] = [{} for _ in range(len(ranges))]

    for i, (start, end) in enumerate(ranges):
        batch = _download_batch(symbols, start, end, timeout=timeout)
        if batch.empty:
            continue
        for symbol in symbols:
            try:
                sym_df = batch[symbol]
            except KeyError:
                continue
            per_range[i][symbol] = _compute_roi_apy(sym_df)

    result: dict = {
        "roi": [],
        "avgRoi": [],
        "apy": [],
        "avgApy": [],
        "roiSeries": [],
        "apySeries": [],
    }
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
        result["roiSeries"].append(hist_rois)
        result["apySeries"].append(hist_apys)

    return result
