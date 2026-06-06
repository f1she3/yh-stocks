"""
French tax rules for CTO, PEA, and Assurance-Vie (UC).
All rates are valid for fiscal year 2025/2026.

References:
  - PFU: Art. 200 A CGI (12.8% IR + 17.2% PS = 30%)
  - PEA: Art. 157, 163 quinquies D CGI — PS-only (17.2%) after 5 years
  - AV UC: Art. 125-0 A CGI — 7.5% IR + 17.2% PS after 8 years, abatement 4600/9200 €
"""

from dataclasses import dataclass

# ---------------------------------------------------------------------------
# Tax constants
# ---------------------------------------------------------------------------

# CTO — Prélèvement Forfaitaire Unique
PFU_IR: float = 0.128
PFU_PS: float = 0.172
PFU_TOTAL: float = PFU_IR + PFU_PS  # 30%

# PEA
PEA_CAP: float = 150_000.0
PEA_PS_RATE: float = 0.172
PEA_MATURITY_YEARS: int = 5

# Assurance-Vie (UC)
AV_MATURITY_YEARS: int = 8
AV_PS_RATE: float = 0.172
AV_IR_RATE_AFTER: float = 0.075   # after 8 years
AV_ABATTEMENT_SINGLE: float = 4_600.0
AV_ABATTEMENT_COUPLE: float = 9_200.0


# ---------------------------------------------------------------------------
# Result type
# ---------------------------------------------------------------------------

@dataclass
class TaxResult:
    net_value: float
    taxes_paid: float
    # Conditional warnings for the UI
    pea_cap_hit_year: int | None = None   # year the PEA 150k€ cap was reached


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _pfu_on_gain(gain: float) -> float:
    return max(0.0, gain) * PFU_TOTAL


# ---------------------------------------------------------------------------
# CTO
# ---------------------------------------------------------------------------

def apply_cto(
    gross_snapshots: list[float],
    contributions_per_year: list[float],
    dividend_yield: float,
    frais_garde_pct: float,
) -> tuple[list[float], list[float], float]:
    """
    Returns (net_values, taxes_per_year, total_fees).

    Strategy:
      - Dividends are taxed each year at PFU 30%.
      - Capital gain on price appreciation taxed at exit (PFU 30%).
      - frais_garde deducted each year on portfolio value.
      - courtage is deducted from contributions upstream in simulation_service.
    """
    net_values: list[float] = []
    taxes_per_year: list[float] = []
    total_fees: float = 0.0
    total_contributions: float = sum(contributions_per_year)
    cumulative_tax: float = 0.0

    for year_idx, gross_val in enumerate(gross_snapshots):
        # Approximate portfolio value at start of year (previous year end, or initial)
        prev = gross_snapshots[year_idx - 1] if year_idx > 0 else gross_val / (1 + dividend_yield)
        annual_dividends = prev * dividend_yield
        div_tax = annual_dividends * PFU_TOTAL

        # frais de garde on portfolio
        garde_fee = gross_val * frais_garde_pct
        total_fees += garde_fee

        net_val = gross_val - garde_fee - cumulative_tax - div_tax
        cumulative_tax += div_tax
        taxes_per_year.append(div_tax)
        net_values.append(net_val)

    # Capital gain tax at exit (on price appreciation only — dividends already taxed)
    total_dividends_paid = sum(gross_snapshots[i] * dividend_yield for i in range(len(gross_snapshots)))
    price_gain = max(0.0, gross_snapshots[-1] - total_contributions - total_dividends_paid)
    exit_tax = price_gain * PFU_TOTAL
    net_values[-1] -= exit_tax
    taxes_per_year[-1] += exit_tax

    return net_values, taxes_per_year, total_fees


# ---------------------------------------------------------------------------
# PEA
# ---------------------------------------------------------------------------

def apply_pea(
    gross_snapshots: list[float],
    contributions_per_year: list[float],
    frais_garde_pct: float,
) -> tuple[list[float], list[float], float, int | None]:
    """
    Returns (net_values, taxes_per_year, total_fees, cap_hit_year).

    - No annual tax.
    - frais_garde deducted each year.
    - At exit: 17.2% PS if horizon >= 5 years, else 30% PFU.
    - Contributions capped at PEA_CAP; excess silently excluded.
    """
    net_values: list[float] = []
    taxes_per_year: list[float] = []
    total_fees: float = 0.0
    cumulative_contributions: float = 0.0
    cap_hit_year: int | None = None

    for year_idx, gross_val in enumerate(gross_snapshots):
        year_contribution = contributions_per_year[year_idx]
        if cumulative_contributions < PEA_CAP:
            allowed = min(year_contribution, PEA_CAP - cumulative_contributions)
            cumulative_contributions += allowed
            if cumulative_contributions >= PEA_CAP and cap_hit_year is None:
                cap_hit_year = year_idx + 1

        garde_fee = gross_val * frais_garde_pct
        total_fees += garde_fee
        net_values.append(gross_val - garde_fee)
        taxes_per_year.append(0.0)

    # Exit tax
    horizon = len(gross_snapshots)
    total_contributions = min(sum(contributions_per_year), PEA_CAP)
    gain = max(0.0, net_values[-1] - total_contributions)
    if horizon >= PEA_MATURITY_YEARS:
        exit_tax = gain * PEA_PS_RATE
    else:
        exit_tax = gain * PFU_TOTAL

    net_values[-1] -= exit_tax
    taxes_per_year[-1] += exit_tax

    return net_values, taxes_per_year, total_fees, cap_hit_year


# ---------------------------------------------------------------------------
# Assurance-Vie (UC)
# ---------------------------------------------------------------------------

def apply_av(
    gross_snapshots: list[float],
    contributions_per_year: list[float],
    frais_gestion_pct: float,
    frais_garde_pct: float,
    is_couple: bool = False,
) -> tuple[list[float], list[float], float]:
    """
    Returns (net_values, taxes_per_year, total_fees).

    - frais_gestion + frais_garde deducted annually (already baked into r_effective_av
      in simulation_service, but we track fees here for display).
    - No annual tax for UC.
    - At exit (rachat total): 17.2% PS on full gain + 7.5% IR on (gain - abatement)
      if horizon >= 8 years. Else 30% PFU.
    - Abatement is per-year-of-redemption: single redemption => one year's abatement.
    """
    net_values: list[float] = []
    taxes_per_year: list[float] = []
    total_fees: float = 0.0
    total_contributions = sum(contributions_per_year)
    abatement = AV_ABATTEMENT_COUPLE if is_couple else AV_ABATTEMENT_SINGLE

    for year_idx, gross_val in enumerate(gross_snapshots):
        gestion_fee = gross_val * frais_gestion_pct
        garde_fee = gross_val * frais_garde_pct
        total_fees += gestion_fee + garde_fee
        net_values.append(gross_val - gestion_fee - garde_fee)
        taxes_per_year.append(0.0)

    # Exit tax
    horizon = len(gross_snapshots)
    gain = max(0.0, net_values[-1] - total_contributions)
    if horizon >= AV_MATURITY_YEARS:
        ps_tax = gain * AV_PS_RATE
        taxable_ir = max(0.0, gain - abatement)
        ir_tax = taxable_ir * AV_IR_RATE_AFTER
        exit_tax = ps_tax + ir_tax
    else:
        exit_tax = gain * PFU_TOTAL

    net_values[-1] -= exit_tax
    taxes_per_year[-1] += exit_tax

    return net_values, taxes_per_year, total_fees
