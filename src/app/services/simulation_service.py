"""
Investment simulation engine.

Runs month-by-month compound growth with periodic contributions,
then delegates tax and fee accounting to tax_service.
"""

from dataclasses import dataclass, field
from math import prod

import numpy_financial as npf

from app.services.tax_service import apply_av, apply_cto, apply_pea


# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------

@dataclass
class SimulationParams:
    apport_initial: float       # initial capital (€)
    versement_mensuel: float    # monthly contribution (€)
    horizon_years: int          # 1-50
    r_annual: float             # geometric mean annual return (decimal, e.g. 0.12)
    avg_apy: float              # geometric mean annual dividend yield (decimal)
    courtage_pct: float         # % fee on each contribution (e.g. 0.001 = 0.1%)
    frais_garde_pct: float      # % annual custody fee on portfolio (e.g. 0.001)
    frais_gestion_av_pct: float # % annual AV management fee (e.g. 0.0075)
    is_couple: bool = False     # AV abatement: couple (9200€) vs single (4600€)


@dataclass
class YearSnapshot:
    year: int
    gross_value: float
    cto_net: float
    pea_net: float
    av_net: float
    cto_taxes: float
    pea_taxes: float
    av_taxes: float
    fees_cto: float
    fees_pea: float
    fees_av: float


@dataclass
class SimulationResult:
    snapshots: list[YearSnapshot]
    cagr: float                     # geometric mean annual return used (%)
    avg_apy_pct: float              # dividend yield used (%)
    cto_irr: float | None
    pea_irr: float | None
    av_irr: float | None
    pea_cap_hit_year: int | None
    pea_cap_warning: bool = field(init=False)

    def __post_init__(self) -> None:
        self.pea_cap_warning = self.pea_cap_hit_year is not None


# ---------------------------------------------------------------------------
# Return rate helpers
# ---------------------------------------------------------------------------

def compute_cagr(roi_series: list[float | None]) -> float:
    """
    Geometric mean (CAGR) from a list of annual ROI percentages.
    Filters None values. Returns 0.0 if no valid data.
    """
    valid = [r / 100.0 for r in roi_series if r is not None]
    if not valid:
        return 0.0
    growth_factors = [1.0 + r for r in valid]
    return prod(growth_factors) ** (1.0 / len(growth_factors)) - 1.0


def portfolio_cagr(roi_series_per_symbol: list[list[float | None]]) -> float:
    """Median CAGR across all symbols (robust to outliers)."""
    cagrs = [compute_cagr(s) for s in roi_series_per_symbol]
    valid = sorted(c for c in cagrs if c is not None)
    if not valid:
        return 0.0
    mid = len(valid) // 2
    if len(valid) % 2 == 0:
        return (valid[mid - 1] + valid[mid]) / 2
    return valid[mid]


def portfolio_avg_apy(apy_series_per_symbol: list[list[float | None]]) -> float:
    """Median geometric APY across all symbols."""
    cagrs = [compute_cagr(s) for s in apy_series_per_symbol]
    valid = sorted(c for c in cagrs if c is not None)
    if not valid:
        return 0.0
    mid = len(valid) // 2
    if len(valid) % 2 == 0:
        return (valid[mid - 1] + valid[mid]) / 2
    return valid[mid]


# ---------------------------------------------------------------------------
# Core simulation loop
# ---------------------------------------------------------------------------

def _simulate_gross(params: SimulationParams) -> tuple[list[float], list[float]]:
    """
    Month-by-month compounding. Returns:
      - gross_snapshots: portfolio value at end of each year (pre-tax, pre-fees)
      - contributions_per_year: sum of net contributions each year (after courtage)
    """
    r_monthly = (1.0 + params.r_annual) ** (1.0 / 12) - 1.0
    portfolio = params.apport_initial
    gross_snapshots: list[float] = []
    contributions_per_year: list[float] = []

    # Initial capital (no courtage on initial apport)
    year_contribs = params.apport_initial

    for year in range(params.horizon_years):
        if year > 0:
            year_contribs = 0.0
        for month in range(12):
            portfolio *= 1.0 + r_monthly
            net_contribution = params.versement_mensuel * (1.0 - params.courtage_pct)
            portfolio += net_contribution
            year_contribs += net_contribution

        gross_snapshots.append(portfolio)
        contributions_per_year.append(year_contribs if year == 0 else params.versement_mensuel * 12 * (1.0 - params.courtage_pct))

    return gross_snapshots, contributions_per_year


def _compute_irr(
    apport: float,
    versement: float,
    net_final: float,
    horizon_years: int,
) -> float | None:
    n_months = horizon_years * 12
    cash_flows = [-apport] + [-versement] * (n_months - 1) + [net_final - versement]
    try:
        monthly_irr = float(npf.irr(cash_flows))
        if monthly_irr != monthly_irr:  # NaN check
            return None
        return (1.0 + monthly_irr) ** 12 - 1.0
    except Exception:
        return None


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------

def run_simulation(params: SimulationParams) -> SimulationResult:
    gross_snapshots, contributions_per_year = _simulate_gross(params)

    # AV uses a lower effective return (frais_gestion drag)
    av_params = SimulationParams(
        apport_initial=params.apport_initial,
        versement_mensuel=params.versement_mensuel,
        horizon_years=params.horizon_years,
        r_annual=max(0.0, params.r_annual - params.frais_gestion_av_pct),
        avg_apy=params.avg_apy,
        courtage_pct=params.courtage_pct,
        frais_garde_pct=params.frais_garde_pct,
        frais_gestion_av_pct=0.0,  # already baked into r_annual above
        is_couple=params.is_couple,
    )
    av_gross, av_contribs = _simulate_gross(av_params)

    cto_nets, cto_taxes, fees_cto = apply_cto(
        gross_snapshots,
        contributions_per_year,
        params.avg_apy,
        params.frais_garde_pct,
    )
    pea_nets, pea_taxes, fees_pea, cap_hit_year = apply_pea(
        gross_snapshots,
        contributions_per_year,
        params.frais_garde_pct,
    )
    av_nets, av_taxes_list, fees_av = apply_av(
        av_gross,
        av_contribs,
        params.frais_gestion_av_pct,
        params.frais_garde_pct,
        params.is_couple,
    )

    snapshots = [
        YearSnapshot(
            year=i + 1,
            gross_value=gross_snapshots[i],
            cto_net=cto_nets[i],
            pea_net=pea_nets[i],
            av_net=av_nets[i],
            cto_taxes=sum(cto_taxes[: i + 1]),
            pea_taxes=sum(pea_taxes[: i + 1]),
            av_taxes=sum(av_taxes_list[: i + 1]),
            fees_cto=fees_cto / params.horizon_years * (i + 1),
            fees_pea=fees_pea / params.horizon_years * (i + 1),
            fees_av=fees_av / params.horizon_years * (i + 1),
        )
        for i in range(params.horizon_years)
    ]

    cto_irr = _compute_irr(params.apport_initial, params.versement_mensuel, cto_nets[-1], params.horizon_years)
    pea_irr = _compute_irr(params.apport_initial, params.versement_mensuel, pea_nets[-1], params.horizon_years)
    av_irr = _compute_irr(params.apport_initial, params.versement_mensuel, av_nets[-1], params.horizon_years)

    return SimulationResult(
        snapshots=snapshots,
        cagr=params.r_annual * 100,
        avg_apy_pct=params.avg_apy * 100,
        cto_irr=cto_irr,
        pea_irr=pea_irr,
        av_irr=av_irr,
        pea_cap_hit_year=cap_hit_year,
    )
