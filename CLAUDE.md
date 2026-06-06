# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

```bash
# Install dependencies
poetry install

# Run the script
poetry run ./src/main.py
```

No linter or test suite is configured.

## Architecture

This is a CLI script that fetches stock data from Yahoo Finance and outputs a CSV with KPIs.

**Entry point:** `src/main.py` - prompts the user (via `rich`) to choose a search type (single stock, country, or index), then delegates to functions in `src/functions.py`.

**`src/functions.py`** contains all business logic:
- `get_companies_list()` - resolves a country or index name to a list of `{names, symbols}` using `pytickersymbols`
- `calc_kpis()` - iterates over symbols and computes ROI, avg ROI, APY, avg APY per ticker
- `kpi_get_roi()` / `kpi_get_apy()` - single-year KPI calculations using `yfinance` history data
- `get_avg_kpi()` - averages a KPI function over N past years; year boundaries are Dec 31 to Dec 31 to avoid yfinance off-by-one quirks

**`src/logger_config.py`** - sets up a color-coded console logger shared across modules.

**Output:** a CSV file written to `output/<name>.csv`, sorted by ROI descending.

## KPI definitions

- **ROI** = (end_price - start_price + dividends) / start_price, expressed as %
- **APY** = dividends / start_price, expressed as %
- Both are calculated from Dec 31 of the previous year to today (or Dec 31 of the current year)
- Avg variants average the single-year value over the past `avg_len` years (default: 10)

## CI

`.github/workflows/main.yml` auto-approves and merges Dependabot PRs for patch/minor updates; major production dependency bumps are flagged with a `question` label instead.
