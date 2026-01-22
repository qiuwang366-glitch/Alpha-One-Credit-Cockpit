"""
Portfolio Analytics Module for Alpha-One Credit Cockpit.

Implements stratified regression analysis for Rich/Cheap bond identification
and various portfolio analytics for fixed income optimization.
"""

import logging
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
from scipy import stats
from scipy.optimize import curve_fit

from ..utils.constants import (
    SECTOR_COLORS,
    MIN_SAMPLES_FOR_REGRESSION,
    Z_SCORE_THRESHOLDS,
    NON_TRADEABLE_ACCOUNTING,
)

logger = logging.getLogger(__name__)


def nelson_siegel(tau: np.ndarray, beta_0: float, beta_1: float, beta_2: float, lambda_: float) -> np.ndarray:
    """
    Nelson-Siegel yield curve model.

    Formula: y(τ) = β₀ + β₁ * [(1-exp(-τ/λ)) / (τ/λ)] + β₂ * [(1-exp(-τ/λ)) / (τ/λ) - exp(-τ/λ)]

    Args:
        tau: Maturity/duration values
        beta_0: Long-term level (asymptotic yield as τ → ∞)
        beta_1: Short-term component (loading on short factor)
        beta_2: Medium-term component (loading on curvature factor)
        lambda_: Decay parameter (controls where curvature peaks)

    Returns:
        Predicted yield values
    """
    # Avoid division by zero
    tau = np.maximum(tau, 1e-6)
    tau_lambda = tau / lambda_

    # Calculate factors
    factor_1 = (1 - np.exp(-tau_lambda)) / tau_lambda
    factor_2 = factor_1 - np.exp(-tau_lambda)

    return beta_0 + beta_1 * factor_1 + beta_2 * factor_2


@dataclass
class RegressionResult:
    """
    Results from sector curve fitting.

    Stores quadratic regression coefficients and statistics for
    the yield-duration relationship within a sector.

    Yield = a * Duration^2 + b * Duration + c
    """

    sector: str
    coefficients: Tuple[float, float, float]  # (a, b, c)
    r_squared: float
    sample_count: int
    duration_range: Tuple[float, float]
    residual_std: float

    @property
    def a(self) -> float:
        """Quadratic coefficient."""
        return self.coefficients[0]

    @property
    def b(self) -> float:
        """Linear coefficient."""
        return self.coefficients[1]

    @property
    def c(self) -> float:
        """Intercept."""
        return self.coefficients[2]

    def predict(self, duration: np.ndarray) -> np.ndarray:
        """Predict yield for given duration values."""
        return self.a * duration**2 + self.b * duration + self.c

    def to_dict(self) -> dict:
        """Convert to dictionary for display."""
        return {
            "Sector": self.sector,
            "R²": f"{self.r_squared:.4f}",
            "Sample Size": self.sample_count,
            "Duration Range": f"{self.duration_range[0]:.1f} - {self.duration_range[1]:.1f}",
            "Residual Std": f"{self.residual_std * 100:.2f}%",  # In percentage
            "Coefficients (a,b,c)": f"({self.a:.6f}, {self.b:.4f}, {self.c:.4f})",
        }


@dataclass
class NelsonSiegelResult:
    """
    Results from Nelson-Siegel curve fitting.

    Stores Nelson-Siegel parameters and statistics for the yield-duration
    relationship within a sector.

    Yield(τ) = β₀ + β₁*f₁(τ) + β₂*f₂(τ)
    where f₁, f₂ are Nelson-Siegel factor loadings
    """

    sector: str
    beta_0: float  # Long-term level
    beta_1: float  # Short-term component
    beta_2: float  # Medium-term/curvature component
    lambda_: float  # Decay parameter
    r_squared: float
    sample_count: int
    duration_range: Tuple[float, float]
    residual_std: float

    def predict(self, duration: np.ndarray) -> np.ndarray:
        """Predict yield for given duration values using Nelson-Siegel."""
        return nelson_siegel(duration, self.beta_0, self.beta_1, self.beta_2, self.lambda_)

    def to_dict(self) -> dict:
        """Convert to dictionary for display."""
        return {
            "Sector": self.sector,
            "R²": f"{self.r_squared:.4f}",
            "Sample Size": self.sample_count,
            "Duration Range": f"{self.duration_range[0]:.1f} - {self.duration_range[1]:.1f}",
            "Residual Std": f"{self.residual_std * 100:.2f}%",
            "β₀ (Long-Term)": f"{self.beta_0 * 100:.2f}%",
            "β₁ (Short-Term)": f"{self.beta_1 * 100:.2f}%",
            "β₂ (Curvature)": f"{self.beta_2 * 100:.2f}%",
            "λ (Decay)": f"{self.lambda_:.2f}",
        }


@dataclass
class PortfolioMetrics:
    """Aggregate portfolio-level metrics."""

    total_aum: float
    weighted_duration: float
    weighted_yield: float
    weighted_net_carry: float
    negative_carry_count: int
    negative_carry_exposure: float
    htim_count: int
    htm_exposure: float
    tradeable_count: int
    tradeable_exposure: float
    sector_exposures: Dict[str, float] = field(default_factory=dict)
    accounting_breakdown: Dict[str, float] = field(default_factory=dict)


class PortfolioAnalyzer:
    """
    Quantitative analyzer for fixed income portfolios.

    Implements:
    - Stratified regression (sector-specific yield curves)
    - Rich/Cheap identification via Z-scores
    - Carry analysis and efficiency metrics
    - Portfolio optimization suggestions

    Example:
        >>> analyzer = PortfolioAnalyzer(df)
        >>> analyzer.fit_sector_curves()
        >>> candidates = analyzer.get_sell_candidates(z_threshold=-1.5)
    """

    def __init__(self, df: pd.DataFrame, model_type: str = "quadratic"):
        """
        Initialize analyzer with cleaned portfolio data.

        Args:
            df: Cleaned DataFrame from DataLoader
            model_type: Type of curve model ("quadratic" or "nelson_siegel")
        """
        self.df = df.copy()
        self.model_type = model_type
        self._regression_results: Dict[str, RegressionResult] = {}
        self._nelson_siegel_results: Dict[str, NelsonSiegelResult] = {}
        self._is_fitted = False

    def fit_sector_curves(
        self,
        min_samples: int = MIN_SAMPLES_FOR_REGRESSION,
        sectors: Optional[List[str]] = None,
    ):
        """
        Fit yield-duration curves for each sector using the specified model.

        For quadratic: Yield = a*Duration² + b*Duration + c
        For Nelson-Siegel: Yield = β₀ + β₁*f₁(τ) + β₂*f₂(τ)

        Args:
            min_samples: Minimum bonds required to fit a curve
            sectors: Specific sectors to fit (None = all)

        Returns:
            Dictionary mapping sector names to result objects
        """
        if sectors is None:
            sectors = self.df["Sector_L1"].unique()

        self._regression_results = {}
        self._nelson_siegel_results = {}

        for sector in sectors:
            sector_df = self.df[self.df["Sector_L1"] == sector]

            if len(sector_df) < min_samples:
                logger.warning(
                    f"Sector '{sector}' has only {len(sector_df)} bonds. "
                    f"Skipping curve fit (min={min_samples})."
                )
                continue

            if self.model_type == "nelson_siegel":
                result = self._fit_nelson_siegel_curve(sector, sector_df)
                if result is not None:
                    self._nelson_siegel_results[sector] = result
            else:  # quadratic
                result = self._fit_single_curve(sector, sector_df)
                if result is not None:
                    self._regression_results[sector] = result

        # Calculate Z-scores after fitting
        self._calculate_z_scores()
        self._is_fitted = True

        results_count = len(self._nelson_siegel_results) if self.model_type == "nelson_siegel" else len(self._regression_results)
        logger.info(f"Fitted {self.model_type} curves for {results_count} sectors")

        return self._nelson_siegel_results if self.model_type == "nelson_siegel" else self._regression_results

    def _fit_single_curve(
        self,
        sector: str,
        sector_df: pd.DataFrame,
    ) -> Optional[RegressionResult]:
        """Fit a single sector curve."""
        # Extract clean data
        mask = sector_df["Duration"].notna() & sector_df["Yield"].notna()
        clean_df = sector_df[mask]

        if len(clean_df) < MIN_SAMPLES_FOR_REGRESSION:
            return None

        x = clean_df["Duration"].values
        y = clean_df["Yield"].values

        try:
            # Fit quadratic: y = ax² + bx + c
            coeffs = np.polyfit(x, y, deg=2)
            a, b, c = coeffs

            # Calculate R-squared
            y_pred = np.polyval(coeffs, x)
            ss_res = np.sum((y - y_pred) ** 2)
            ss_tot = np.sum((y - np.mean(y)) ** 2)
            r_squared = 1 - (ss_res / ss_tot) if ss_tot > 0 else 0

            # Calculate residual standard deviation
            residuals = y - y_pred
            residual_std = np.std(residuals)

            return RegressionResult(
                sector=sector,
                coefficients=(a, b, c),
                r_squared=r_squared,
                sample_count=len(clean_df),
                duration_range=(x.min(), x.max()),
                residual_std=residual_std,
            )

        except Exception as e:
            logger.error(f"Failed to fit curve for sector '{sector}': {e}")
            return None

    def _fit_nelson_siegel_curve(
        self,
        sector: str,
        sector_df: pd.DataFrame,
    ) -> Optional[NelsonSiegelResult]:
        """
        Fit a Nelson-Siegel curve for a single sector.

        Uses scipy.optimize.curve_fit to calibrate the four parameters:
        β₀, β₁, β₂, λ
        """
        # Extract clean data
        mask = sector_df["Duration"].notna() & sector_df["Yield"].notna()
        clean_df = sector_df[mask]

        if len(clean_df) < MIN_SAMPLES_FOR_REGRESSION:
            return None

        x = clean_df["Duration"].values
        y = clean_df["Yield"].values

        try:
            # Initial parameter guesses
            # β₀: use mean yield as proxy for long-term level
            # β₁: use difference between short and long yields
            # β₂: curvature, start with small value
            # λ: decay parameter, typically around mean duration
            y_mean = np.mean(y)
            y_first = y[np.argmin(x)] if len(x) > 0 else y_mean
            y_last = y[np.argmax(x)] if len(x) > 0 else y_mean

            p0 = [
                y_mean,              # β₀
                y_first - y_mean,    # β₁
                0.01,                # β₂
                max(np.mean(x), 1.0) # λ (ensure positive)
            ]

            # Parameter bounds (all yields in decimal, e.g., 0.05 = 5%)
            bounds = (
                [-0.5, -0.5, -0.5, 0.1],      # lower bounds
                [0.5, 0.5, 0.5, 50.0]         # upper bounds
            )

            # Fit using curve_fit
            params, _ = curve_fit(
                nelson_siegel,
                x,
                y,
                p0=p0,
                bounds=bounds,
                maxfev=5000,
            )

            beta_0, beta_1, beta_2, lambda_ = params

            # Calculate R-squared
            y_pred = nelson_siegel(x, beta_0, beta_1, beta_2, lambda_)
            ss_res = np.sum((y - y_pred) ** 2)
            ss_tot = np.sum((y - np.mean(y)) ** 2)
            r_squared = 1 - (ss_res / ss_tot) if ss_tot > 0 else 0

            # Calculate residual standard deviation
            residuals = y - y_pred
            residual_std = np.std(residuals)

            return NelsonSiegelResult(
                sector=sector,
                beta_0=beta_0,
                beta_1=beta_1,
                beta_2=beta_2,
                lambda_=lambda_,
                r_squared=r_squared,
                sample_count=len(clean_df),
                duration_range=(x.min(), x.max()),
                residual_std=residual_std,
            )

        except Exception as e:
            logger.error(f"Failed to fit Nelson-Siegel curve for sector '{sector}': {e}")
            return None

    def _calculate_z_scores(self) -> None:
        """Calculate Z-scores for all bonds based on fitted curves."""
        self.df["Model_Yield"] = np.nan
        self.df["Residual"] = np.nan
        self.df["Z_Score"] = np.nan

        # Choose the appropriate results dict based on model type
        results = self._nelson_siegel_results if self.model_type == "nelson_siegel" else self._regression_results

        for sector, result in results.items():
            mask = self.df["Sector_L1"] == sector

            # Calculate model yield
            duration = self.df.loc[mask, "Duration"].values
            model_yield = result.predict(duration)
            self.df.loc[mask, "Model_Yield"] = model_yield

            # Calculate residuals
            actual_yield = self.df.loc[mask, "Yield"].values
            residuals = actual_yield - model_yield
            self.df.loc[mask, "Residual"] = residuals

            # Calculate Z-scores (standardized residuals)
            if result.residual_std > 0:
                z_scores = residuals / result.residual_std
                self.df.loc[mask, "Z_Score"] = z_scores

    def get_regression_results(self):
        """Get fitted regression results by sector."""
        if not self._is_fitted:
            raise ValueError("Must call fit_sector_curves() first")
        return self._nelson_siegel_results if self.model_type == "nelson_siegel" else self._regression_results

    def get_curve_points(
        self,
        sector: str,
        n_points: int = 100,
    ) -> Tuple[np.ndarray, np.ndarray]:
        """
        Get points for plotting a sector curve.

        Args:
            sector: Sector name
            n_points: Number of points to generate

        Returns:
            Tuple of (duration_array, yield_array)
        """
        # Choose the appropriate results dict
        results = self._nelson_siegel_results if self.model_type == "nelson_siegel" else self._regression_results

        if sector not in results:
            raise ValueError(f"No curve fitted for sector '{sector}'")

        result = results[sector]
        x = np.linspace(result.duration_range[0], result.duration_range[1], n_points)
        y = result.predict(x)

        return x, y

    def get_sell_candidates(
        self,
        z_threshold: float = -1.5,
        max_net_carry: Optional[float] = None,
        exclude_htm: bool = True,
    ) -> pd.DataFrame:
        """
        Identify sell candidates: rich bonds with low carry.

        Args:
            z_threshold: Maximum Z-score (negative = rich/expensive)
            max_net_carry: Maximum net carry threshold
            exclude_htm: Exclude HTM (non-tradeable) bonds

        Returns:
            DataFrame of sell candidates
        """
        if not self._is_fitted:
            raise ValueError("Must call fit_sector_curves() first")

        mask = self.df["Z_Score"] < z_threshold

        if max_net_carry is not None:
            mask &= self.df["Net_Carry"] < max_net_carry

        if exclude_htm:
            mask &= self.df["Is_Tradeable"]

        candidates = self.df[mask].copy()

        return candidates.sort_values("Z_Score").reset_index(drop=True)

    def get_bleeding_assets(self, exclude_htm: bool = True) -> pd.DataFrame:
        """
        Identify "bleeding" assets with negative carry.

        These bonds have Yield < FTP, meaning they cost more to fund
        than they return.

        Args:
            exclude_htm: Exclude HTM bonds

        Returns:
            DataFrame of negative carry bonds
        """
        mask = self.df["Net_Carry"] < 0

        if exclude_htm:
            mask &= self.df["Is_Tradeable"]

        return self.df[mask].sort_values("Net_Carry").reset_index(drop=True)

    def get_buy_candidates(
        self,
        z_threshold: float = 1.5,
        min_net_carry: Optional[float] = None,
        min_liquidity: int = 3,
    ) -> pd.DataFrame:
        """
        Identify buy candidates: cheap bonds with good carry.

        Args:
            z_threshold: Minimum Z-score (positive = cheap)
            min_net_carry: Minimum net carry required
            min_liquidity: Minimum liquidity score

        Returns:
            DataFrame of buy candidates
        """
        if not self._is_fitted:
            raise ValueError("Must call fit_sector_curves() first")

        mask = self.df["Z_Score"] > z_threshold
        mask &= self.df["Liquidity_Proxy"] >= min_liquidity

        if min_net_carry is not None:
            mask &= self.df["Net_Carry"] > min_net_carry

        candidates = self.df[mask].copy()

        return candidates.sort_values("Z_Score", ascending=False).reset_index(drop=True)

    def calculate_portfolio_metrics(self) -> PortfolioMetrics:
        """Calculate aggregate portfolio metrics."""
        df = self.df
        total_aum = df["Nominal_USD"].sum()

        # Weighted calculations
        def weighted_avg(col):
            return (df[col] * df["Nominal_USD"]).sum() / total_aum if total_aum > 0 else 0

        # Sector exposures
        sector_exposures = (
            df.groupby("Sector_L1")["Nominal_USD"]
            .sum()
            .sort_values(ascending=False)
            .to_dict()
        )

        # Accounting breakdown
        accounting_breakdown = (
            df.groupby("Accounting")["Nominal_USD"]
            .sum()
            .sort_values(ascending=False)
            .to_dict()
        )

        # Negative carry exposure
        negative_carry_mask = df["Net_Carry"] < 0
        negative_carry_exposure = df.loc[negative_carry_mask, "Nominal_USD"].sum()

        # HTM exposure
        htm_mask = df["Accounting"] == "HTM"
        htim_exposure = df.loc[htm_mask, "Nominal_USD"].sum()

        # Tradeable exposure
        tradeable_exposure = df.loc[df["Is_Tradeable"], "Nominal_USD"].sum()

        return PortfolioMetrics(
            total_aum=total_aum,
            weighted_duration=weighted_avg("Duration"),
            weighted_yield=weighted_avg("Yield"),
            weighted_net_carry=weighted_avg("Net_Carry"),
            negative_carry_count=negative_carry_mask.sum(),
            negative_carry_exposure=negative_carry_exposure,
            htim_count=htm_mask.sum(),
            htm_exposure=htim_exposure,
            tradeable_count=df["Is_Tradeable"].sum(),
            tradeable_exposure=tradeable_exposure,
            sector_exposures=sector_exposures,
            accounting_breakdown=accounting_breakdown,
        )

    def get_sector_summary(self) -> pd.DataFrame:
        """Get summary statistics by sector."""
        if not self._is_fitted:
            self.fit_sector_curves()

        summary = (
            self.df.groupby("Sector_L1")
            .agg(
                {
                    "Nominal_USD": ["sum", "count"],
                    "Duration": "mean",
                    "Yield": "mean",
                    "Net_Carry": "mean",
                    "Z_Score": ["mean", "std"],
                }
            )
            .round(4)
        )

        # Flatten column names
        summary.columns = [
            "Total_Exposure",
            "Count",
            "Avg_Duration",
            "Avg_Yield",
            "Avg_Net_Carry",
            "Avg_Z_Score",
            "Z_Score_Std",
        ]

        return summary.sort_values("Total_Exposure", ascending=False)

    def generate_executive_summary(self) -> str:
        """
        Generate a markdown executive summary for management.

        Returns:
            Markdown formatted summary
        """
        metrics = self.calculate_portfolio_metrics()
        sector_summary = self.get_sector_summary()

        # Find richest sectors (negative avg Z-score)
        richest_sectors = (
            self.df.groupby("Sector_L1")["Z_Score"]
            .mean()
            .sort_values()
            .head(3)
        )

        # Format AUM
        def format_usd(value):
            if value >= 1e9:
                return f"${value/1e9:.2f}B"
            elif value >= 1e6:
                return f"${value/1e6:.2f}M"
            else:
                return f"${value:,.0f}"

        summary = f"""
## Portfolio Executive Summary

### Overview
| Metric | Value |
|--------|-------|
| **Total AUM** | {format_usd(metrics.total_aum)} |
| **Number of Holdings** | {len(self.df):,} |
| **Weighted Duration** | {metrics.weighted_duration:.2f} years |
| **Weighted Yield** | {metrics.weighted_yield * 100:.2f}% |
| **Weighted Net Carry** | {metrics.weighted_net_carry * 100:.2f}% |

### Risk Flags
| Flag | Count | Exposure |
|------|-------|----------|
| **Negative Carry (Bleeding)** | {metrics.negative_carry_count} | {format_usd(metrics.negative_carry_exposure)} |
| **HTM (Non-Tradeable)** | {metrics.htim_count} | {format_usd(metrics.htm_exposure)} |

### Top 3 "Richest" Sectors (Potential Sell Pressure)
Sectors with negative average Z-scores are trading expensive relative to their curves.

| Sector | Avg Z-Score | Interpretation |
|--------|-------------|----------------|
"""
        for sector, z in richest_sectors.items():
            interpretation = "Very Rich" if z < -1 else "Moderately Rich" if z < -0.5 else "Slightly Rich"
            summary += f"| {sector} | {z:.2f} | {interpretation} |\n"

        # Liquidity profile
        high_liq = (self.df["Liquidity_Proxy"] >= 5).sum()
        low_liq = (self.df["Liquidity_Proxy"] < 5).sum()

        summary += f"""
### Liquidity Profile
- **High Liquidity (Score ≥ 5):** {high_liq} bonds ({high_liq/len(self.df)*100:.1f}%)
- **Lower Liquidity (Score < 5):** {low_liq} bonds ({low_liq/len(self.df)*100:.1f}%)

### Sector Allocation
| Sector | Exposure | % of Portfolio |
|--------|----------|----------------|
"""
        for sector, exposure in list(metrics.sector_exposures.items())[:5]:
            pct = exposure / metrics.total_aum * 100
            summary += f"| {sector} | {format_usd(exposure)} | {pct:.1f}% |\n"

        summary += """
---
*Report generated by Alpha-One Credit Cockpit*
"""
        return summary

    def get_filtered_data(
        self,
        exclude_htm: bool = True,
        sectors: Optional[List[str]] = None,
        min_liquidity: int = 1,
    ) -> pd.DataFrame:
        """
        Get filtered portfolio data based on criteria.

        Args:
            exclude_htm: Exclude HTM bonds
            sectors: Filter to specific sectors
            min_liquidity: Minimum liquidity score

        Returns:
            Filtered DataFrame
        """
        mask = pd.Series([True] * len(self.df), index=self.df.index)

        if exclude_htm:
            mask &= self.df["Is_Tradeable"]

        if sectors:
            mask &= self.df["Sector_L1"].isin(sectors)

        mask &= self.df["Liquidity_Proxy"] >= min_liquidity

        return self.df[mask].copy()

    @property
    def sectors(self) -> List[str]:
        """Get list of unique sectors."""
        return self.df["Sector_L1"].unique().tolist()

    def get_color_for_sector(self, sector: str) -> str:
        """Get consistent color for a sector."""
        return SECTOR_COLORS.get(sector, "#999999")
