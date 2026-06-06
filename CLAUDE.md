# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

```bash
# Install all dependencies (including dev tools)
uv sync --extra dev

# Run the web app locally (no Docker)
uv run uvicorn src.app.server:app --reload --port 8000

# Run with Docker (dev mode, hot-reload)
docker compose up --build

# Run in production mode
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d

# Lint
uv run ruff check src/ tests/
uv run ruff format src/ tests/

# Type check
uv run mypy src/app/

# Tests
uv run pytest tests/ --ignore=tests/smoke/
```

## Architecture

This is a **Dockerized web application** (FastAPI + Jinja2 + HTMX + Plotly) that lets French retail investors simulate investment returns with accurate tax treatment for CTO, PEA, and Assurance-vie.

### Entry point

`src/app/server.py` — FastAPI app factory. The lifespan context manager initializes the diskcache and config. Run via uvicorn.

The old `src/main.py` is retired (kept for git history only).

### Source layout

```
src/
  config.py               — AppConfig dataclass, reads env vars
  functions.py            — yfinance batch data fetching + KPI computation (reused core)
  logger_config.py        — TTY-aware logger (color in terminal, JSON in container)
  main.py                 — RETIRED CLI entry point
  app/
    server.py             — FastAPI factory, lifespan, router mount
    routes/
      index.py            — GET /  (form page)
      simulate.py         — POST /simulate  (HTMX endpoint, returns HTML fragment)
    services/
      stock_service.py    — resolves companies + calls calc_kpis + cache
      simulation_service.py — compound growth simulation (CAGR, monthly compounding, IRR)
      tax_service.py      — French tax rules: CTO/PEA/AV
    charts/
      kpi_comparison.py   — Plotly horizontal bar chart
      projection.py       — Plotly gross vs net projection chart
      price_history.py    — Plotly 5y normalized price history
    cache/
      yfinance_cache.py   — diskcache get_or_fetch wrapper
    models/
      inputs.py           — SimulationRequest Pydantic model
      results.py          — KpiRow dataclass
    templates/            — Jinja2 templates (base, index, partials)
    static/style.css      — single CSS file, no framework
```

### KPI definitions

- **ROI** = (end_price - start_price + dividends) / start_price, as %
- **APY** = dividends / start_price, as %
- Both use Dec 31 to Dec 31 yearly boundaries, avg over `avg_len` years (default 10)
- `roiSeries` / `apySeries`: raw per-year lists returned by `calc_kpis()` for CAGR computation

### Simulation model

- Return rate: **geometric mean (CAGR)** from historical per-year ROI series — not arithmetic mean
- Monthly compounding: `(1 + r_annual)^(1/12) - 1` per month
- Contributions: monthly versements minus courtage % added each month
- Fees: `frais_garde` and `frais_gestion_av` deducted annually from portfolio value

### French tax rules (2025/2026)

| Enveloppe | Pendant | A la sortie |
|---|---|---|
| CTO | Dividendes : PFU 30%/an | Plus-value : PFU 30% |
| PEA | Aucun (plafond 150 000 €) | 17,2% PS si >=5 ans, sinon PFU 30% |
| AV (UC) | Aucun | >=8 ans : 17,2% PS + 7,5% IR (apres abattement 4 600 €/9 200 €) |

### Caching

`diskcache.Cache` at `CACHE_DIR` (default `/tmp/yh-stocks-cache`). TTL: 1h for KPIs, 24h for company lists. Bind-mounted in Docker so cache survives restarts.

### CI

`.github/workflows/ci.yml` — 4 jobs: lint, typecheck, test (parallel) then build-and-scan (Trivy). On `main`, pushes image to GHCR.

`.github/workflows/dependabot-automerge.yml` — auto-approves patch/minor; flags major prod deps. Action pinned to SHA.

`.github/workflows/scheduled-scan.yml` — weekly Trivy scan of published image.
