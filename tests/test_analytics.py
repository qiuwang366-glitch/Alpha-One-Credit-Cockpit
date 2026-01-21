"""
Tests for the Analytics module.
"""

import numpy as np
import pandas as pd
import pytest

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.module_b.analytics import PortfolioAnalyzer, RegressionResult


class TestRegressionResult:
    """Test suite for RegressionResult."""

    def test_predict(self):
        """Test yield prediction from regression result."""
        result = RegressionResult(
            sector="MBS",
            coefficients=(0.001, 0.01, 0.03),  # a, b, c
            r_squared=0.95,
            sample_count=50,
            duration_range=(1.0, 10.0),
            residual_std=0.005,
        )

        # Test prediction: y = 0.001 * x^2 + 0.01 * x + 0.03
        duration = np.array([5.0])
        expected = 0.001 * 25 + 0.01 * 5 + 0.03  # 0.105
        predicted = result.predict(duration)

        assert predicted[0] == pytest.approx(expected, rel=1e-6)

    def test_coefficients_properties(self):
        """Test coefficient property accessors."""
        result = RegressionResult(
            sector="Corps",
            coefficients=(0.002, 0.015, 0.025),
            r_squared=0.90,
            sample_count=30,
            duration_range=(0.5, 8.0),
            residual_std=0.008,
        )

        assert result.a == 0.002
        assert result.b == 0.015
        assert result.c == 0.025


class TestPortfolioAnalyzer:
    """Test suite for PortfolioAnalyzer."""

    @pytest.fixture
    def sample_portfolio(self):
        """Create a sample portfolio DataFrame for testing."""
        np.random.seed(42)
        n_bonds = 100

        sectors = np.random.choice(["MBS", "Corps", "Fins", "Rates"], n_bonds)
        durations = np.random.uniform(1, 10, n_bonds)

        # Generate yields with sector-specific curves + noise
        yields = []
        for i in range(n_bonds):
            sector = sectors[i]
            dur = durations[i]

            if sector == "MBS":
                base_yield = 0.001 * dur**2 + 0.005 * dur + 0.035
            elif sector == "Corps":
                base_yield = 0.0008 * dur**2 + 0.008 * dur + 0.032
            elif sector == "Fins":
                base_yield = 0.0012 * dur**2 + 0.006 * dur + 0.038
            else:  # Rates
                base_yield = 0.0005 * dur**2 + 0.004 * dur + 0.030

            yields.append(base_yield + np.random.normal(0, 0.005))

        data = {
            "Sector_L1": sectors,
            "Sector_L2": ["Sub"] * n_bonds,
            "Ticker": [f"BOND{i}" for i in range(n_bonds)],
            "Name": [f"Bond {i}" for i in range(n_bonds)],
            "Accounting": np.random.choice(["AFS", "HTM", "Fair Value"], n_bonds, p=[0.6, 0.3, 0.1]),
            "Nominal_USD": np.random.uniform(1e6, 50e6, n_bonds),
            "Duration": durations,
            "Yield": yields,
            "OAS": np.random.uniform(20, 150, n_bonds),
            "FTP": np.random.uniform(0.03, 0.045, n_bonds),
            "FTP_Missing": [False] * n_bonds,
            "Liquidity_Proxy": np.random.choice([3, 5], n_bonds),
            "Net_Carry": np.array(yields) - np.random.uniform(0.03, 0.045, n_bonds),
            "Carry_Efficiency": np.zeros(n_bonds),  # Will be calculated
            "Is_Tradeable": [acc != "HTM" for acc in np.random.choice(["AFS", "HTM", "Fair Value"], n_bonds, p=[0.6, 0.3, 0.1])],
        }

        df = pd.DataFrame(data)
        df["Carry_Efficiency"] = df["Net_Carry"] / df["Duration"]
        df["Is_Tradeable"] = df["Accounting"] != "HTM"

        return df

    def test_fit_sector_curves(self, sample_portfolio):
        """Test fitting curves for each sector."""
        analyzer = PortfolioAnalyzer(sample_portfolio)
        results = analyzer.fit_sector_curves()

        # Should have results for all sectors with sufficient data
        assert len(results) > 0

        # Check each result has valid data
        for sector, result in results.items():
            assert result.sample_count >= 5
            assert 0 <= result.r_squared <= 1
            assert result.residual_std > 0

    def test_z_score_calculation(self, sample_portfolio):
        """Test Z-score calculation after curve fitting."""
        analyzer = PortfolioAnalyzer(sample_portfolio)
        analyzer.fit_sector_curves()

        # Z-scores should be calculated
        assert "Z_Score" in analyzer.df.columns

        # Most Z-scores should be between -3 and 3 for normal distribution
        z_scores = analyzer.df["Z_Score"].dropna()
        assert (np.abs(z_scores) < 4).mean() > 0.95

    def test_get_sell_candidates(self, sample_portfolio):
        """Test identification of sell candidates."""
        analyzer = PortfolioAnalyzer(sample_portfolio)
        analyzer.fit_sector_curves()

        candidates = analyzer.get_sell_candidates(z_threshold=-1.5, exclude_htm=True)

        # All candidates should have Z-score < -1.5
        if len(candidates) > 0:
            assert (candidates["Z_Score"] < -1.5).all()

            # All candidates should be tradeable
            assert candidates["Is_Tradeable"].all()

    def test_get_bleeding_assets(self, sample_portfolio):
        """Test identification of negative carry assets."""
        # Modify some bonds to have negative carry
        sample_portfolio = sample_portfolio.copy()
        sample_portfolio.loc[:10, "Net_Carry"] = -0.005

        analyzer = PortfolioAnalyzer(sample_portfolio)
        analyzer.fit_sector_curves()

        bleeding = analyzer.get_bleeding_assets(exclude_htm=True)

        # All bleeding assets should have negative net carry
        if len(bleeding) > 0:
            assert (bleeding["Net_Carry"] < 0).all()

    def test_get_buy_candidates(self, sample_portfolio):
        """Test identification of buy candidates."""
        analyzer = PortfolioAnalyzer(sample_portfolio)
        analyzer.fit_sector_curves()

        candidates = analyzer.get_buy_candidates(z_threshold=1.5)

        # All candidates should have Z-score > 1.5
        if len(candidates) > 0:
            assert (candidates["Z_Score"] > 1.5).all()

    def test_calculate_portfolio_metrics(self, sample_portfolio):
        """Test portfolio metrics calculation."""
        analyzer = PortfolioAnalyzer(sample_portfolio)
        analyzer.fit_sector_curves()

        metrics = analyzer.calculate_portfolio_metrics()

        assert metrics.total_aum > 0
        assert 0 < metrics.weighted_duration < 15
        assert 0 < metrics.weighted_yield < 0.15
        assert len(metrics.sector_exposures) > 0

    def test_get_sector_summary(self, sample_portfolio):
        """Test sector summary generation."""
        analyzer = PortfolioAnalyzer(sample_portfolio)
        analyzer.fit_sector_curves()

        summary = analyzer.get_sector_summary()

        assert "Total_Exposure" in summary.columns
        assert "Count" in summary.columns
        assert "Avg_Z_Score" in summary.columns

    def test_generate_executive_summary(self, sample_portfolio):
        """Test executive summary generation."""
        analyzer = PortfolioAnalyzer(sample_portfolio)
        analyzer.fit_sector_curves()

        summary = analyzer.generate_executive_summary()

        # Should be a markdown string
        assert isinstance(summary, str)
        assert "##" in summary  # Contains headers
        assert "AUM" in summary

    def test_get_filtered_data(self, sample_portfolio):
        """Test data filtering."""
        analyzer = PortfolioAnalyzer(sample_portfolio)

        # Filter by HTM exclusion
        filtered = analyzer.get_filtered_data(exclude_htm=True)
        assert (filtered["Accounting"] != "HTM").all()

        # Filter by sectors
        filtered = analyzer.get_filtered_data(sectors=["MBS", "Corps"])
        assert filtered["Sector_L1"].isin(["MBS", "Corps"]).all()

        # Filter by liquidity
        filtered = analyzer.get_filtered_data(min_liquidity=5)
        assert (filtered["Liquidity_Proxy"] >= 5).all()

    def test_get_curve_points(self, sample_portfolio):
        """Test curve points generation for plotting."""
        analyzer = PortfolioAnalyzer(sample_portfolio)
        analyzer.fit_sector_curves()

        results = analyzer.get_regression_results()
        if results:
            sector = list(results.keys())[0]
            x, y = analyzer.get_curve_points(sector, n_points=50)

            assert len(x) == 50
            assert len(y) == 50
            assert x[0] < x[-1]  # Sorted ascending

    def test_sectors_property(self, sample_portfolio):
        """Test sectors property."""
        analyzer = PortfolioAnalyzer(sample_portfolio)

        sectors = analyzer.sectors
        assert isinstance(sectors, list)
        assert len(sectors) > 0

    def test_min_samples_threshold(self):
        """Test that sectors with few bonds are skipped."""
        # Create data with one sector having only 2 bonds
        data = {
            "Sector_L1": ["MBS"] * 20 + ["Rare"] * 2,
            "Ticker": [f"BOND{i}" for i in range(22)],
            "Accounting": ["AFS"] * 22,
            "Nominal_USD": [1e6] * 22,
            "Duration": list(np.linspace(1, 10, 22)),
            "Yield": list(np.linspace(0.03, 0.06, 22)),
            "Net_Carry": [0.01] * 22,
            "Is_Tradeable": [True] * 22,
            "Liquidity_Proxy": [5] * 22,
        }
        df = pd.DataFrame(data)

        analyzer = PortfolioAnalyzer(df)
        results = analyzer.fit_sector_curves(min_samples=5)

        # "Rare" sector should not have a curve
        assert "MBS" in results
        assert "Rare" not in results


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
