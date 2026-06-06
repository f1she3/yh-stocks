import sys
import os

# functions.py lives in src/, which is on sys.path via server.py lifespan
import diskcache
import yfinance as yf

from app.cache.yfinance_cache import get_or_fetch
from app.models.results import KpiRow
from functions import calc_kpis, get_companies_list


def resolve_companies(name: str, search_type: str) -> dict:
    if search_type == "stock":
        ticker = yf.Ticker(name)
        info = ticker.info
        long_name = info.get("longName", name)
        return {"names": [long_name], "symbols": [name]}
    elif search_type == "country":
        return get_companies_list(name, is_country=True)
    else:
        return get_companies_list(name, is_index=True)


def get_kpis(
    name: str,
    search_type: str,
    avg_len: int,
    cache: diskcache.Cache,
    cache_ttl: int,
    yf_timeout: int,
) -> tuple[list[KpiRow], list[list[float | None]], list[list[float | None]]]:
    """
    Returns (kpi_rows, roi_series_per_symbol, apy_series_per_symbol).
    """
    companies_key = f"companies:{search_type}:{name}"
    companies = get_or_fetch(
        cache,
        companies_key,
        lambda: resolve_companies(name, search_type),
        ttl=86400,  # 24h — company lists change rarely
    )

    names: list[str] = companies["names"]
    symbols: list[str] = companies["symbols"]

    kpis_key = f"kpis:{search_type}:{name}:{avg_len}"
    raw = get_or_fetch(
        cache,
        kpis_key,
        lambda: calc_kpis(symbols, avg_len=avg_len, timeout=yf_timeout),
        ttl=cache_ttl,
    )

    rows = [
        KpiRow(
            name=names[i],
            symbol=symbols[i],
            roi_pct=raw["roi"][i],
            avg_roi_pct=raw["avgRoi"][i],
            apy_pct=raw["apy"][i],
            avg_apy_pct=raw["avgApy"][i],
        )
        for i in range(len(symbols))
        if raw["roi"][i] is not None
    ]

    valid_indices = [i for i in range(len(symbols)) if raw["roi"][i] is not None]
    roi_series = [raw["roiSeries"][i] for i in valid_indices]
    apy_series = [raw["apySeries"][i] for i in valid_indices]

    return rows, roi_series, apy_series
