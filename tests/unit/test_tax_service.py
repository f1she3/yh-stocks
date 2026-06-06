"""Unit tests for the French tax calculation engine."""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../src"))

from app.services.tax_service import (
    PFU_TOTAL,
    PEA_PS_RATE,
    AV_ABATTEMENT_SINGLE,
    apply_cto,
    apply_pea,
    apply_av,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _even_contributions(annual_total: float, years: int) -> list[float]:
    return [annual_total] * years


# ---------------------------------------------------------------------------
# CTO tests
# ---------------------------------------------------------------------------

class TestCTO:
    def test_no_gain_no_tax(self):
        """Zero dividend yield and zero gain => only frais_garde deducted."""
        gross = [10_000.0, 10_000.0]
        contribs = [5_000.0, 5_000.0]
        net_vals, taxes, fees = apply_cto(gross, contribs, 0.0, 0.0)
        assert all(t == 0.0 for t in taxes)
        assert net_vals[-1] == gross[-1]

    def test_dividend_tax_applied_annually(self):
        """With dividend yield, tax should be positive each year."""
        gross = [10_000.0, 11_000.0]
        contribs = [5_000.0, 600.0]
        net_vals, taxes, fees = apply_cto(gross, contribs, 0.03, 0.0)
        # Year 0: dividends = gross[0] / (1 + 0.03) * 0.03, taxed at 30%
        assert taxes[0] > 0

    def test_frais_garde_deducted(self):
        """frais_garde reduces net value."""
        gross = [10_000.0, 10_000.0]
        contribs = [5_000.0, 5_000.0]
        net_vals_with_fee, _, fees = apply_cto(gross, contribs, 0.0, 0.001)
        net_vals_no_fee, _, _ = apply_cto(gross, contribs, 0.0, 0.0)
        assert fees > 0
        assert net_vals_with_fee[-1] < net_vals_no_fee[-1]

    def test_exit_tax_on_price_gain(self):
        """Price appreciation at exit is taxed at PFU 30%."""
        # No dividends, all gain is price appreciation
        initial = 10_000.0
        final = 20_000.0
        gross = [15_000.0, final]
        contribs = [initial, 0.0]
        net_vals, taxes, _ = apply_cto(gross, contribs, 0.0, 0.0)
        price_gain = final - initial
        expected_exit_tax = price_gain * PFU_TOTAL
        assert abs(taxes[-1] - expected_exit_tax) < 1.0


# ---------------------------------------------------------------------------
# PEA tests
# ---------------------------------------------------------------------------

class TestPEA:
    def test_no_annual_tax(self):
        """No taxes due until exit."""
        gross = [10_000.0] * 6
        contribs = _even_contributions(2_000.0, 6)
        net_vals, taxes, fees, _ = apply_pea(gross, contribs, 0.0)
        # Only the last year has exit tax
        assert all(t == 0.0 for t in taxes[:-1])

    def test_ps_only_after_5_years(self):
        """After 5 years exit: only PEA_PS_RATE (17.2%) on gain."""
        final = 20_000.0
        gross = [12_000.0] * 4 + [15_000.0, final]
        contribs = _even_contributions(1_000.0, 6)
        total_contrib = 6_000.0
        net_vals, taxes, fees, _ = apply_pea(gross, contribs, 0.0)
        gain = final - total_contrib
        expected_tax = gain * PEA_PS_RATE
        assert abs(taxes[-1] - expected_tax) < 0.01

    def test_pfu_before_5_years(self):
        """Before 5 years exit: PFU 30% on gain."""
        final = 15_000.0
        gross = [11_000.0, 13_000.0, final]
        contribs = _even_contributions(2_000.0, 3)
        total_contrib = 6_000.0
        net_vals, taxes, fees, _ = apply_pea(gross, contribs, 0.0)
        gain = final - total_contrib
        expected_tax = gain * PFU_TOTAL
        assert abs(taxes[-1] - expected_tax) < 0.01

    def test_cap_hit_year_reported(self):
        """PEA cap (150k€) hit should be reported."""
        # 80k per year => cap hit in year 2
        gross = [80_000.0, 160_000.0, 200_000.0, 240_000.0, 280_000.0, 320_000.0]
        contribs = [80_000.0] * 6
        _, _, _, cap_hit_year = apply_pea(gross, contribs, 0.0)
        assert cap_hit_year == 2  # year 2 pushes cumulative to 160k > 150k

    def test_no_tax_on_negative_gain(self):
        """No tax when portfolio is underwater."""
        gross = [5_000.0] * 6
        contribs = _even_contributions(10_000.0, 6)
        _, taxes, _, _ = apply_pea(gross, contribs, 0.0)
        assert taxes[-1] == 0.0


# ---------------------------------------------------------------------------
# AV tests
# ---------------------------------------------------------------------------

class TestAV:
    def test_reduced_tax_after_8_years(self):
        """After 8 years: 17.2% PS + 7.5% IR on gain above abatement."""
        final_net = 50_000.0
        gross = [5_000.0 * i for i in range(1, 9)]  # 8 years
        contribs = _even_contributions(2_000.0, 8)
        total_contrib = 16_000.0
        net_vals, taxes, _ = apply_av(gross, contribs, 0.0, 0.0, is_couple=False)
        gain = net_vals[-1] + taxes[-1] - total_contrib  # reconstruct pre-tax gain
        expected_ps = gain * 0.172
        expected_ir = max(0.0, gain - AV_ABATTEMENT_SINGLE) * 0.075
        expected_total = expected_ps + expected_ir
        assert abs(taxes[-1] - expected_total) < 0.01

    def test_pfu_before_8_years(self):
        """Before 8 years: PFU 30% on gain."""
        final = 20_000.0
        gross = [10_000.0, 15_000.0, final]
        contribs = _even_contributions(3_000.0, 3)
        total_contrib = 9_000.0
        net_vals, taxes, _ = apply_av(gross, contribs, 0.0, 0.0)
        gain = net_vals[-1] + taxes[-1] - total_contrib
        expected = max(0.0, gain) * PFU_TOTAL
        assert abs(taxes[-1] - expected) < 0.01

    def test_couple_abatement_larger(self):
        """Couple abatement (9200€) reduces IR more than single (4600€)."""
        gross = [5_000.0 * i for i in range(1, 9)]
        contribs = _even_contributions(1_000.0, 8)
        _, taxes_single, _ = apply_av(gross, contribs, 0.0, 0.0, is_couple=False)
        _, taxes_couple, _ = apply_av(gross, contribs, 0.0, 0.0, is_couple=True)
        assert taxes_couple[-1] < taxes_single[-1]

    def test_frais_gestion_reduces_net(self):
        """frais_gestion should reduce net value compared to no fees."""
        gross = [10_000.0] * 8
        contribs = _even_contributions(1_000.0, 8)
        net_with, _, fees_with = apply_av(gross, contribs, 0.0075, 0.0)
        net_without, _, fees_without = apply_av(gross, contribs, 0.0, 0.0)
        assert fees_with > fees_without
        assert net_with[-1] < net_without[-1]

    def test_no_tax_on_loss(self):
        """No exit tax when portfolio value is below total contributions."""
        gross = [1_000.0] * 8
        contribs = _even_contributions(5_000.0, 8)
        _, taxes, _ = apply_av(gross, contribs, 0.0, 0.0)
        assert taxes[-1] == 0.0
