"""Unit tests for the simulation engine."""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../src"))

from app.services.simulation_service import (
    SimulationParams,
    compute_cagr,
    portfolio_cagr,
    run_simulation,
)


class TestComputeCAGR:
    def test_single_year(self):
        assert abs(compute_cagr([10.0]) - 0.10) < 1e-9

    def test_filters_none(self):
        result = compute_cagr([None, 20.0, None])
        assert abs(result - 0.20) < 1e-9

    def test_all_none_returns_zero(self):
        assert compute_cagr([None, None]) == 0.0

    def test_geometric_less_than_arithmetic(self):
        """Geometric mean < arithmetic mean for volatile returns."""
        series = [50.0, -33.33]  # +50% then -33.33% = ~0%
        cagr = compute_cagr(series)
        arithmetic = sum(r for r in series if r is not None) / 2 / 100
        assert cagr < arithmetic

    def test_symmetric_growth(self):
        """10% per year for 2 years => CAGR exactly 10%."""
        assert abs(compute_cagr([10.0, 10.0]) - 0.10) < 1e-9


class TestPortfolioCAGR:
    def test_median_of_two(self):
        series = [[10.0], [20.0]]
        result = portfolio_cagr(series)
        assert abs(result - 0.15) < 1e-9


class TestRunSimulation:
    def _base_params(self, **kwargs) -> SimulationParams:
        defaults = dict(
            apport_initial=10_000.0,
            versement_mensuel=500.0,
            horizon_years=10,
            r_annual=0.08,
            avg_apy=0.02,
            courtage_pct=0.001,
            frais_garde_pct=0.001,
            frais_gestion_av_pct=0.0075,
            is_couple=False,
        )
        defaults.update(kwargs)
        return SimulationParams(**defaults)

    def test_gross_grows_monotonically(self):
        params = self._base_params()
        result = run_simulation(params)
        values = [s.gross_value for s in result.snapshots]
        assert all(values[i] < values[i + 1] for i in range(len(values) - 1))

    def test_net_less_than_gross(self):
        params = self._base_params(horizon_years=10)
        result = run_simulation(params)
        last = result.snapshots[-1]
        assert last.cto_net < last.gross_value
        assert last.pea_net < last.gross_value
        assert last.av_net < last.gross_value

    def test_pea_better_than_cto_long_horizon(self):
        """PEA (17.2% PS only) should outperform CTO (30% PFU) after 5y."""
        params = self._base_params(horizon_years=10, avg_apy=0.03)
        result = run_simulation(params)
        last = result.snapshots[-1]
        assert last.pea_net > last.cto_net

    def test_irr_positive_for_positive_return(self):
        params = self._base_params(r_annual=0.10)
        result = run_simulation(params)
        assert result.cto_irr is not None and result.cto_irr > 0
        assert result.pea_irr is not None and result.pea_irr > 0
        assert result.av_irr is not None and result.av_irr > 0

    def test_snapshot_count_matches_horizon(self):
        params = self._base_params(horizon_years=15)
        result = run_simulation(params)
        assert len(result.snapshots) == 15

    def test_year_numbers_sequential(self):
        params = self._base_params(horizon_years=5)
        result = run_simulation(params)
        assert [s.year for s in result.snapshots] == [1, 2, 3, 4, 5]

    def test_pea_cap_warning_triggered(self):
        """150€/month * 12 * 50 years still won't hit 150k, but big apport will."""
        params = self._base_params(apport_initial=149_000.0, versement_mensuel=1_000.0, horizon_years=10)
        result = run_simulation(params)
        assert result.pea_cap_warning is True
        assert result.pea_cap_hit_year == 1  # 149k + 12*1k = 161k > 150k in year 1

    def test_zero_return_still_runs(self):
        params = self._base_params(r_annual=0.0, avg_apy=0.0)
        result = run_simulation(params)
        assert len(result.snapshots) == 10
