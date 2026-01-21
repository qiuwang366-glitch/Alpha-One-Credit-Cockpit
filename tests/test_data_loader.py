"""
Tests for the DataLoader module.
"""

import numpy as np
import pandas as pd
import pytest

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.module_b.data_loader import DataLoader, DataValidationError


class TestDataLoader:
    """Test suite for DataLoader."""

    def test_load_from_dataframe(self):
        """Test loading from an existing DataFrame."""
        # Create sample data with bilingual columns
        data = {
            "分类1": ["MBS", "Corps", "Fins"],
            "分类2": ["Agency", "Tech", "Banks"],
            "TICKER": ["FNMA", "AAPL", "JPM"],
            "债券名称": ["Fannie Mae", "Apple Inc", "JPMorgan"],
            "AccSection": ["AFS", "HTM", "AFS"],
            "Nominal（USD）": ["1,000,000", "2,000,000", "3,000,000"],
            "Duration": [5.0, 3.0, 2.5],
            "EffectiveYield": ["4.5%", "3.8%", "4.2%"],
            "OAS": [50, 45, 55],
            "FTP Rate": ["4.0%", "3.5%", "3.8%"],
        }
        df_input = pd.DataFrame(data)

        loader = DataLoader()
        df = loader.load(df_input)

        # Check column renaming
        assert "Sector_L1" in df.columns
        assert "Sector_L2" in df.columns
        assert "Ticker" in df.columns
        assert "Name" in df.columns
        assert "Accounting" in df.columns
        assert "Nominal_USD" in df.columns
        assert "Yield" in df.columns

        # Check data cleaning
        assert df["Nominal_USD"].iloc[0] == 1000000.0
        assert df["Yield"].iloc[0] == pytest.approx(0.045, rel=1e-3)

        # Check enrichment
        assert "Net_Carry" in df.columns
        assert "Carry_Efficiency" in df.columns
        assert "Is_Tradeable" in df.columns
        assert "Liquidity_Proxy" in df.columns

    def test_nominal_cleaning(self):
        """Test cleaning of Nominal_USD column."""
        data = {
            "分类1": ["MBS", "Corps"],
            "TICKER": ["A", "B"],
            "AccSection": ["AFS", "AFS"],
            "Nominal（USD）": ["1,234,567.89", "$2,000,000"],
            "Duration": [5.0, 3.0],
            "EffectiveYield": ["4.5%", "3.8%"],
        }
        df_input = pd.DataFrame(data)

        loader = DataLoader()
        df = loader.load(df_input)

        assert df["Nominal_USD"].iloc[0] == pytest.approx(1234567.89, rel=1e-3)
        assert df["Nominal_USD"].iloc[1] == pytest.approx(2000000.0, rel=1e-3)

    def test_yield_cleaning(self):
        """Test cleaning of Yield column."""
        data = {
            "分类1": ["MBS", "Corps", "Fins"],
            "TICKER": ["A", "B", "C"],
            "AccSection": ["AFS", "AFS", "AFS"],
            "Nominal（USD）": [1000000, 2000000, 3000000],
            "Duration": [5.0, 3.0, 2.5],
            "EffectiveYield": ["4.5%", "0.038", "5"],  # Various formats
        }
        df_input = pd.DataFrame(data)

        loader = DataLoader()
        df = loader.load(df_input)

        assert df["Yield"].iloc[0] == pytest.approx(0.045, rel=1e-3)
        assert df["Yield"].iloc[1] == pytest.approx(0.038, rel=1e-3)
        assert df["Yield"].iloc[2] == pytest.approx(0.05, rel=1e-3)

    def test_accounting_standardization(self):
        """Test standardization of Accounting values."""
        data = {
            "分类1": ["MBS", "Corps", "Fins", "Rates"],
            "TICKER": ["A", "B", "C", "D"],
            "AccSection": ["htm", "AFS", "FAIR VALUE", "fv"],
            "Nominal（USD）": [1000000, 2000000, 3000000, 4000000],
            "Duration": [5.0, 3.0, 2.5, 4.0],
            "EffectiveYield": ["4.5%", "3.8%", "4.2%", "4.0%"],
        }
        df_input = pd.DataFrame(data)

        loader = DataLoader()
        df = loader.load(df_input)

        assert df["Accounting"].iloc[0] == "HTM"
        assert df["Accounting"].iloc[1] == "AFS"
        assert df["Accounting"].iloc[2] == "Fair Value"
        assert df["Accounting"].iloc[3] == "Fair Value"

    def test_is_tradeable_flag(self):
        """Test Is_Tradeable flag based on accounting."""
        data = {
            "分类1": ["MBS", "Corps"],
            "TICKER": ["A", "B"],
            "AccSection": ["HTM", "AFS"],
            "Nominal（USD）": [1000000, 2000000],
            "Duration": [5.0, 3.0],
            "EffectiveYield": ["4.5%", "3.8%"],
        }
        df_input = pd.DataFrame(data)

        loader = DataLoader()
        df = loader.load(df_input)

        assert df["Is_Tradeable"].iloc[0] == False  # HTM
        assert df["Is_Tradeable"].iloc[1] == True   # AFS

    def test_liquidity_proxy(self):
        """Test Liquidity_Proxy calculation."""
        data = {
            "分类1": ["MBS", "Corps"],
            "TICKER": ["A", "B"],
            "AccSection": ["AFS", "AFS"],
            "Nominal（USD）": [5000000, 15000000],  # Below and above $10M
            "Duration": [5.0, 3.0],
            "EffectiveYield": ["4.5%", "3.8%"],
        }
        df_input = pd.DataFrame(data)

        loader = DataLoader()
        df = loader.load(df_input)

        assert df["Liquidity_Proxy"].iloc[0] == 3  # Below threshold
        assert df["Liquidity_Proxy"].iloc[1] == 5  # Above threshold

    def test_net_carry_calculation(self):
        """Test Net_Carry calculation."""
        data = {
            "分类1": ["MBS", "Corps"],
            "TICKER": ["A", "B"],
            "AccSection": ["AFS", "AFS"],
            "Nominal（USD）": [1000000, 2000000],
            "Duration": [5.0, 3.0],
            "EffectiveYield": ["5%", "3%"],
            "FTP Rate": ["4%", "4%"],  # Yield > FTP and Yield < FTP
        }
        df_input = pd.DataFrame(data)

        loader = DataLoader()
        df = loader.load(df_input)

        assert df["Net_Carry"].iloc[0] == pytest.approx(0.01, rel=1e-3)   # Positive carry
        assert df["Net_Carry"].iloc[1] == pytest.approx(-0.01, rel=1e-3)  # Negative carry

    def test_quality_report(self):
        """Test data quality report generation."""
        data = {
            "分类1": ["MBS", "Corps"],
            "TICKER": ["A", "B"],
            "AccSection": ["AFS", "AFS"],
            "Nominal（USD）": [1000000, 2000000],
            "Duration": [5.0, 3.0],
            "EffectiveYield": ["4.5%", "3.8%"],
            "FTP Rate": [np.nan, "4%"],  # One missing FTP
        }
        df_input = pd.DataFrame(data)

        loader = DataLoader()
        df = loader.load(df_input)
        report = loader.get_quality_report()

        assert report.total_rows == 2
        assert report.ftp_missing_count == 1
        assert "A" in report.ftp_missing_tickers

    def test_missing_required_columns(self):
        """Test error on missing required columns."""
        data = {
            "分类1": ["MBS"],
            "TICKER": ["A"],
            # Missing AccSection, Nominal, Duration, Yield
        }
        df_input = pd.DataFrame(data)

        loader = DataLoader()
        with pytest.raises(DataValidationError):
            loader.load(df_input)


class TestCarryEfficiency:
    """Test Carry Efficiency calculations."""

    def test_carry_efficiency_normal(self):
        """Test normal carry efficiency calculation."""
        data = {
            "分类1": ["MBS"],
            "TICKER": ["A"],
            "AccSection": ["AFS"],
            "Nominal（USD）": [1000000],
            "Duration": [5.0],
            "EffectiveYield": ["5%"],
            "FTP Rate": ["4%"],
        }
        df_input = pd.DataFrame(data)

        loader = DataLoader()
        df = loader.load(df_input)

        # Net Carry = 0.05 - 0.04 = 0.01
        # Carry Efficiency = 0.01 / 5.0 = 0.002
        assert df["Carry_Efficiency"].iloc[0] == pytest.approx(0.002, rel=1e-3)

    def test_carry_efficiency_zero_duration(self):
        """Test carry efficiency with zero duration."""
        data = {
            "分类1": ["MBS"],
            "TICKER": ["A"],
            "AccSection": ["AFS"],
            "Nominal（USD）": [1000000],
            "Duration": [0.0],  # Zero duration
            "EffectiveYield": ["5%"],
            "FTP Rate": ["4%"],
        }
        df_input = pd.DataFrame(data)

        loader = DataLoader()
        df = loader.load(df_input)

        # Should be NaN due to division by zero
        assert pd.isna(df["Carry_Efficiency"].iloc[0])


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
