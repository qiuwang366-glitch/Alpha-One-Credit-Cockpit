"""
Financial Data Module for Alpha-One Credit Cockpit.

Handles quarterly financial fundamentals loading, metric calculation,
and mapping between bond tickers and equity tickers.

Supports Bloomberg Terminal-style fundamental analysis for credit analysis.
"""

import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


@dataclass
class QuarterlyMetrics:
    """
    Quarterly financial metrics for a single period.

    All leverage metrics are unitless multiples (x).
    All amounts in original currency units.
    """
    date: pd.Timestamp
    year: int
    quarter: int
    revenue: float
    ebitda: float
    total_liabilities: float
    cash: float
    net_int_exp: float
    net_debt_proxy: float  # Total_Liabilities - Cash
    net_leverage: Optional[float]  # Net_Debt / EBITDA
    interest_coverage: Optional[float]  # EBITDA / Net_Int_Exp
    revenue_qoq_growth: Optional[float]  # Quarter-over-Quarter growth rate


@dataclass
class IssuerFundamentals:
    """
    Complete fundamental data for an issuer.

    Contains historical quarterly metrics and latest quarter summary.
    """
    equity_ticker: str
    issuer_name: str
    bond_ticker: str
    quarterly_data: List[QuarterlyMetrics]

    @property
    def latest_quarter(self) -> Optional[QuarterlyMetrics]:
        """Get most recent quarter data."""
        if not self.quarterly_data:
            return None
        return self.quarterly_data[-1]

    @property
    def last_8_quarters(self) -> List[QuarterlyMetrics]:
        """Get last 8 quarters for trend analysis."""
        return self.quarterly_data[-8:] if len(self.quarterly_data) >= 8 else self.quarterly_data

    def get_trend_series(self, metric_name: str) -> Tuple[List[str], List[float]]:
        """
        Extract time series for a specific metric.

        Args:
            metric_name: Name of the metric attribute (e.g., 'net_leverage', 'revenue')

        Returns:
            Tuple of (date_labels, values)
        """
        quarters = self.last_8_quarters
        dates = [f"{q.year}Q{q.quarter}" for q in quarters]
        values = [getattr(q, metric_name) for q in quarters]

        # Filter out None values
        filtered = [(d, v) for d, v in zip(dates, values) if v is not None and not pd.isna(v)]
        if not filtered:
            return [], []

        dates_filtered, values_filtered = zip(*filtered)
        return list(dates_filtered), list(values_filtered)


class FinancialDataLoader:
    """
    Loader for quarterly financial fundamentals.

    Handles:
    - Loading bond-to-equity ticker mapping
    - Loading quarterly financial statements
    - Calculating leverage and coverage metrics
    - Handling missing data gracefully

    Example:
        >>> loader = FinancialDataLoader()
        >>> loader.load_data()
        >>> fundamentals = loader.get_issuer_fundamentals("AAPL")
    """

    def __init__(self, data_dir: Optional[Path] = None):
        """
        Initialize financial data loader.

        Args:
            data_dir: Path to data directory. If None, uses default 'data' folder.
        """
        self.data_dir = data_dir or Path(__file__).parent.parent.parent / "data"
        self.bond_equity_map: Optional[pd.DataFrame] = None
        self.quarterly_financials: Optional[pd.DataFrame] = None
        self._issuer_cache: Dict[str, IssuerFundamentals] = {}

    def load_data(self) -> bool:
        """
        Load all financial data files.

        Returns:
            True if successful, False otherwise
        """
        try:
            # Load bond-equity mapping
            map_path = self.data_dir / "bond_equity_map.csv"
            if not map_path.exists():
                logger.warning(f"Bond equity map not found: {map_path}")
                return False

            self.bond_equity_map = pd.read_csv(map_path, encoding='utf-8-sig')
            logger.info(f"Loaded {len(self.bond_equity_map)} bond-equity mappings")

            # Load quarterly financials
            financials_path = self.data_dir / "quarterly_financials.csv"
            if not financials_path.exists():
                logger.warning(f"Quarterly financials not found: {financials_path}")
                return False

            self.quarterly_financials = pd.read_csv(financials_path, encoding='utf-8-sig')
            self.quarterly_financials['Date'] = pd.to_datetime(self.quarterly_financials['Date'])

            # Clean numeric columns - handle NaN and empty strings
            numeric_cols = ['Revenue', 'EBITDA', 'Total_Liabilities', 'Cash', 'Net_Int_Exp']
            for col in numeric_cols:
                self.quarterly_financials[col] = pd.to_numeric(
                    self.quarterly_financials[col],
                    errors='coerce'
                )

            # Sort by date
            self.quarterly_financials = self.quarterly_financials.sort_values(['Equity_Ticker', 'Date'])

            logger.info(f"Loaded {len(self.quarterly_financials)} quarterly records")

            # Build issuer cache
            self._build_issuer_cache()

            return True

        except Exception as e:
            logger.error(f"Error loading financial data: {e}")
            return False

    def _build_issuer_cache(self) -> None:
        """Build cache of issuer fundamentals for fast lookup."""
        if self.bond_equity_map is None or self.quarterly_financials is None:
            return

        self._issuer_cache = {}

        for _, row in self.bond_equity_map.iterrows():
            bond_ticker = row['Bond_Ticker']
            equity_ticker = row['Equity_Ticker']
            issuer_name = row['Issuer_Name']

            # Skip if equity ticker is missing or invalid
            if pd.isna(equity_ticker) or equity_ticker.strip() == '' or equity_ticker == 'N/A':
                continue

            # Get quarterly data for this equity ticker
            equity_data = self.quarterly_financials[
                self.quarterly_financials['Equity_Ticker'] == equity_ticker
            ].copy()

            if len(equity_data) == 0:
                continue

            # Calculate metrics for each quarter
            quarterly_metrics = []
            prev_revenue = None

            for idx, q_row in equity_data.iterrows():
                # Calculate Net Debt Proxy
                liabilities = q_row['Total_Liabilities']
                cash = q_row['Cash']
                net_debt_proxy = liabilities - cash if pd.notna(liabilities) and pd.notna(cash) else np.nan

                # Calculate Net Leverage (handle zero/negative EBITDA gracefully)
                ebitda = q_row['EBITDA']
                net_leverage = None
                if pd.notna(net_debt_proxy) and pd.notna(ebitda) and ebitda > 0:
                    net_leverage = net_debt_proxy / ebitda

                # Calculate Interest Coverage (handle zero interest expense)
                net_int_exp = q_row['Net_Int_Exp']
                interest_coverage = None
                if pd.notna(ebitda) and pd.notna(net_int_exp) and net_int_exp != 0:
                    # Use absolute value of interest expense for coverage ratio
                    interest_coverage = ebitda / abs(net_int_exp)

                # Calculate Revenue QoQ Growth
                revenue = q_row['Revenue']
                revenue_qoq = None
                if prev_revenue is not None and pd.notna(revenue) and pd.notna(prev_revenue) and prev_revenue > 0:
                    revenue_qoq = (revenue - prev_revenue) / prev_revenue
                prev_revenue = revenue

                metrics = QuarterlyMetrics(
                    date=q_row['Date'],
                    year=int(q_row['Year']),
                    quarter=int(q_row['Quarter']),
                    revenue=revenue if pd.notna(revenue) else 0.0,
                    ebitda=ebitda if pd.notna(ebitda) else 0.0,
                    total_liabilities=liabilities if pd.notna(liabilities) else 0.0,
                    cash=cash if pd.notna(cash) else 0.0,
                    net_int_exp=net_int_exp if pd.notna(net_int_exp) else 0.0,
                    net_debt_proxy=net_debt_proxy if pd.notna(net_debt_proxy) else 0.0,
                    net_leverage=net_leverage,
                    interest_coverage=interest_coverage,
                    revenue_qoq_growth=revenue_qoq
                )
                quarterly_metrics.append(metrics)

            # Create IssuerFundamentals object
            fundamentals = IssuerFundamentals(
                equity_ticker=equity_ticker,
                issuer_name=issuer_name,
                bond_ticker=bond_ticker,
                quarterly_data=quarterly_metrics
            )

            # Cache by bond ticker
            self._issuer_cache[bond_ticker] = fundamentals

        logger.info(f"Built cache for {len(self._issuer_cache)} issuers with fundamental data")

    def get_issuer_fundamentals(self, bond_ticker: str) -> Optional[IssuerFundamentals]:
        """
        Get fundamental data for a bond issuer.

        Args:
            bond_ticker: Bond ticker symbol

        Returns:
            IssuerFundamentals object or None if not found
        """
        # Extract base ticker (handle complex ticker formats)
        base_ticker = bond_ticker.split()[0] if " " in bond_ticker else bond_ticker

        return self._issuer_cache.get(base_ticker)

    def has_fundamentals(self, bond_ticker: str) -> bool:
        """Check if fundamental data exists for a bond ticker."""
        return self.get_issuer_fundamentals(bond_ticker) is not None

    def get_available_tickers(self) -> List[str]:
        """Get list of all bond tickers with fundamental data."""
        return list(self._issuer_cache.keys())

    def get_coverage_stats(self) -> Dict[str, int]:
        """Get statistics on fundamental data coverage."""
        if self.bond_equity_map is None:
            return {}

        total_bonds = len(self.bond_equity_map)
        bonds_with_fundamentals = len(self._issuer_cache)

        return {
            "total_bonds": total_bonds,
            "bonds_with_fundamentals": bonds_with_fundamentals,
            "coverage_rate": bonds_with_fundamentals / total_bonds if total_bonds > 0 else 0.0
        }
