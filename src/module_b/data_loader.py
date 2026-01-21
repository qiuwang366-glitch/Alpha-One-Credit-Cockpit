"""
Data Loader Module for Alpha-One Credit Cockpit.

Handles ingestion and cleaning of messy, bilingual portfolio data.
Transforms raw CSV exports into clean, analysis-ready DataFrames.
"""

import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional, Union

import numpy as np
import pandas as pd

from ..utils.constants import (
    COLUMN_MAPPING,
    REQUIRED_COLUMNS,
    DEFAULT_FTP,
    LIQUIDITY_THRESHOLD,
    LIQUIDITY_HIGH,
    LIQUIDITY_LOW,
    NON_TRADEABLE_ACCOUNTING,
)

logger = logging.getLogger(__name__)


class DataValidationError(Exception):
    """Raised when data validation fails."""
    pass


@dataclass
class DataQualityReport:
    """Report on data quality issues encountered during loading."""

    total_rows: int = 0
    rows_after_cleaning: int = 0
    ftp_missing_count: int = 0
    ftp_missing_tickers: list = field(default_factory=list)
    nominal_parse_errors: int = 0
    yield_parse_errors: int = 0
    duration_zero_count: int = 0
    unknown_sectors: list = field(default_factory=list)
    unknown_accounting: list = field(default_factory=list)

    def to_dict(self) -> dict:
        """Convert report to dictionary for display."""
        return {
            "Total Rows Loaded": self.total_rows,
            "Rows After Cleaning": self.rows_after_cleaning,
            "Data Retention Rate": f"{self.rows_after_cleaning / max(self.total_rows, 1) * 100:.1f}%",
            "FTP Missing (Flagged)": self.ftp_missing_count,
            "Nominal Parse Errors": self.nominal_parse_errors,
            "Yield Parse Errors": self.yield_parse_errors,
            "Zero Duration Bonds": self.duration_zero_count,
        }

    def has_warnings(self) -> bool:
        """Check if there are any data quality warnings."""
        return (
            self.ftp_missing_count > 0
            or self.nominal_parse_errors > 0
            or self.yield_parse_errors > 0
            or len(self.unknown_sectors) > 0
            or len(self.unknown_accounting) > 0
        )


class DataLoader:
    """
    Robust data loader for fixed income portfolio data.

    Handles:
    - Bilingual column names (Chinese/English)
    - Dirty numeric data (commas, percentage signs, strings)
    - Missing values with intelligent defaults
    - Data enrichment (Liquidity, Net Carry, Carry Efficiency)

    Example:
        >>> loader = DataLoader()
        >>> df = loader.load("portfolio.csv")
        >>> report = loader.get_quality_report()
    """

    def __init__(self, strict_mode: bool = False):
        """
        Initialize the data loader.

        Args:
            strict_mode: If True, raise errors on data quality issues.
                        If False, attempt to clean and continue.
        """
        self.strict_mode = strict_mode
        self._quality_report: Optional[DataQualityReport] = None
        self._raw_df: Optional[pd.DataFrame] = None
        self._clean_df: Optional[pd.DataFrame] = None

    def load(
        self,
        source: Union[str, Path, pd.DataFrame],
        encoding: str = "utf-8",
    ) -> pd.DataFrame:
        """
        Load and clean portfolio data from various sources.

        Args:
            source: File path, Path object, or existing DataFrame
            encoding: File encoding (default utf-8, try 'gbk' for Chinese files)

        Returns:
            Cleaned and enriched DataFrame ready for analysis

        Raises:
            DataValidationError: If required columns are missing or data is invalid
        """
        self._quality_report = DataQualityReport()

        # Step 1: Load raw data
        df = self._load_raw(source, encoding)
        self._raw_df = df.copy()
        self._quality_report.total_rows = len(df)

        logger.info(f"Loaded {len(df)} rows from source")

        # Step 2: Rename columns (bilingual mapping)
        df = self._rename_columns(df)

        # Step 3: Validate required columns exist
        self._validate_required_columns(df)

        # Step 4: Clean numeric columns
        df = self._clean_nominal(df)
        df = self._clean_yield(df)
        df = self._clean_duration(df)
        df = self._clean_oas(df)
        df = self._clean_ftp(df)

        # Step 5: Clean categorical columns
        df = self._clean_accounting(df)
        df = self._clean_sectors(df)

        # Step 6: Data enrichment
        df = self._enrich_data(df)

        # Step 7: Final validation and cleanup
        df = self._final_cleanup(df)

        self._quality_report.rows_after_cleaning = len(df)
        self._clean_df = df

        logger.info(f"Data cleaning complete. {len(df)} rows retained.")

        if self._quality_report.has_warnings():
            logger.warning("Data quality issues detected. Check quality report.")

        return df

    def load_from_upload(self, uploaded_file) -> pd.DataFrame:
        """
        Load data from Streamlit uploaded file object.

        Args:
            uploaded_file: Streamlit UploadedFile object

        Returns:
            Cleaned DataFrame
        """
        # Try UTF-8 first, then GBK for Chinese files
        try:
            df = pd.read_csv(uploaded_file, encoding="utf-8")
        except UnicodeDecodeError:
            uploaded_file.seek(0)  # Reset file pointer
            df = pd.read_csv(uploaded_file, encoding="gbk")

        return self.load(df)

    def get_quality_report(self) -> Optional[DataQualityReport]:
        """Get the data quality report from the last load operation."""
        return self._quality_report

    def get_raw_data(self) -> Optional[pd.DataFrame]:
        """Get the raw data before cleaning."""
        return self._raw_df

    def _load_raw(
        self,
        source: Union[str, Path, pd.DataFrame],
        encoding: str,
    ) -> pd.DataFrame:
        """Load raw data from source."""
        if isinstance(source, pd.DataFrame):
            return source.copy()

        path = Path(source)
        if not path.exists():
            raise DataValidationError(f"File not found: {path}")

        # Try specified encoding, fall back to alternatives
        encodings_to_try = [encoding, "gbk", "gb2312", "utf-8-sig"]

        for enc in encodings_to_try:
            try:
                return pd.read_csv(path, encoding=enc)
            except UnicodeDecodeError:
                continue

        raise DataValidationError(
            f"Could not decode file with encodings: {encodings_to_try}"
        )

    def _rename_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        """Apply bilingual column mapping."""
        # Create case-insensitive mapping
        df_cols = {col.strip(): col for col in df.columns}

        rename_map = {}
        for source_col, target_col in COLUMN_MAPPING.items():
            # Try exact match first
            if source_col in df.columns:
                rename_map[source_col] = target_col
            # Try stripped match
            elif source_col.strip() in df_cols:
                rename_map[df_cols[source_col.strip()]] = target_col
            # Check if target already exists (English source)
            elif target_col in df.columns:
                pass  # Already named correctly

        if rename_map:
            df = df.rename(columns=rename_map)
            logger.debug(f"Renamed columns: {rename_map}")

        return df

    def _validate_required_columns(self, df: pd.DataFrame) -> None:
        """Validate that required columns exist."""
        missing = set(REQUIRED_COLUMNS) - set(df.columns)

        if missing:
            available = list(df.columns)
            raise DataValidationError(
                f"Missing required columns: {missing}. "
                f"Available columns: {available}"
            )

    def _clean_nominal(self, df: pd.DataFrame) -> pd.DataFrame:
        """Clean Nominal_USD column: remove commas, convert to float."""
        if "Nominal_USD" not in df.columns:
            return df

        def parse_nominal(val):
            if pd.isna(val):
                return np.nan
            if isinstance(val, (int, float)):
                return float(val)

            # String cleaning
            s = str(val).strip()
            s = s.replace(",", "").replace("$", "").replace(" ", "")

            # Handle parentheses as negative (accounting notation)
            if s.startswith("(") and s.endswith(")"):
                s = "-" + s[1:-1]

            try:
                return float(s)
            except ValueError:
                return np.nan

        original_valid = df["Nominal_USD"].notna().sum()
        df["Nominal_USD"] = df["Nominal_USD"].apply(parse_nominal)
        new_valid = df["Nominal_USD"].notna().sum()

        self._quality_report.nominal_parse_errors = original_valid - new_valid

        return df

    def _clean_yield(self, df: pd.DataFrame) -> pd.DataFrame:
        """Clean Yield column: remove %, convert to decimal."""
        if "Yield" not in df.columns:
            return df

        def parse_yield(val):
            if pd.isna(val):
                return np.nan
            if isinstance(val, (int, float)):
                # Assume already in decimal if < 1, else in percentage
                return float(val) if val < 1 else float(val) / 100

            s = str(val).strip()
            s = s.replace("%", "").replace(" ", "")

            try:
                val_float = float(s)
                # Convert from percentage to decimal if > 1
                # (yields above 100% are extremely rare)
                return val_float / 100 if val_float > 1 else val_float
            except ValueError:
                return np.nan

        original_valid = df["Yield"].notna().sum()
        df["Yield"] = df["Yield"].apply(parse_yield)
        new_valid = df["Yield"].notna().sum()

        self._quality_report.yield_parse_errors = original_valid - new_valid

        return df

    def _clean_duration(self, df: pd.DataFrame) -> pd.DataFrame:
        """Clean Duration column."""
        if "Duration" not in df.columns:
            return df

        df["Duration"] = pd.to_numeric(df["Duration"], errors="coerce")

        # Track zero durations (problematic for carry efficiency)
        self._quality_report.duration_zero_count = (df["Duration"] == 0).sum()

        return df

    def _clean_oas(self, df: pd.DataFrame) -> pd.DataFrame:
        """Clean OAS (Option-Adjusted Spread) column."""
        if "OAS" not in df.columns:
            df["OAS"] = np.nan
            return df

        # OAS is typically in basis points
        df["OAS"] = pd.to_numeric(df["OAS"], errors="coerce")

        return df

    def _clean_ftp(self, df: pd.DataFrame) -> pd.DataFrame:
        """Clean FTP Rate column: fill NaN with default, flag rows."""
        if "FTP" not in df.columns:
            df["FTP"] = DEFAULT_FTP
            df["FTP_Missing"] = True
            self._quality_report.ftp_missing_count = len(df)
            return df

        # Parse FTP similar to yield
        def parse_ftp(val):
            if pd.isna(val):
                return np.nan
            if isinstance(val, (int, float)):
                return float(val) if val < 1 else float(val) / 100

            s = str(val).strip().replace("%", "")
            try:
                val_float = float(s)
                return val_float / 100 if val_float > 1 else val_float
            except ValueError:
                return np.nan

        df["FTP"] = df["FTP"].apply(parse_ftp)

        # Flag and fill missing FTP
        ftp_missing_mask = df["FTP"].isna()
        df["FTP_Missing"] = ftp_missing_mask

        self._quality_report.ftp_missing_count = ftp_missing_mask.sum()
        self._quality_report.ftp_missing_tickers = (
            df.loc[ftp_missing_mask, "Ticker"].tolist()
            if "Ticker" in df.columns
            else []
        )

        df["FTP"] = df["FTP"].fillna(DEFAULT_FTP)

        return df

    def _clean_accounting(self, df: pd.DataFrame) -> pd.DataFrame:
        """Clean and validate Accounting classification."""
        if "Accounting" not in df.columns:
            df["Accounting"] = "Unknown"
            return df

        # Standardize values
        accounting_map = {
            "HTM": "HTM",
            "HM": "HTM",  # Common typo
            "HOLD TO MATURITY": "HTM",
            "HOLDTOMATURITY": "HTM",
            "AFS": "AFS",
            "AVAILABLE FOR SALE": "AFS",
            "AVAILABLEFORSALE": "AFS",
            "FAIR VALUE": "Fair Value",
            "FAIRVALUE": "Fair Value",
            "FV": "Fair Value",
            "FVPL": "Fair Value",
            "FVOCI": "AFS",  # Fair Value through OCI -> treat as AFS
        }

        df["Accounting"] = df["Accounting"].fillna("Unknown").astype(str).str.strip().str.upper()
        df["Accounting"] = df["Accounting"].map(
            lambda x: accounting_map.get(x, x.title())
        )

        # Track unknown accounting types
        known_types = {"HTM", "AFS", "Fair Value", "Unknown"}
        unknown_mask = ~df["Accounting"].isin(known_types)
        self._quality_report.unknown_accounting = (
            df.loc[unknown_mask, "Accounting"].unique().tolist()
        )

        return df

    def _clean_sectors(self, df: pd.DataFrame) -> pd.DataFrame:
        """Clean sector columns."""
        for col in ["Sector_L1", "Sector_L2"]:
            if col in df.columns:
                df[col] = df[col].fillna("Other").astype(str).str.strip()

        # Standard sector names
        sector_map = {
            "CORPS": "Corps",
            "CORPORATES": "Corps",
            "CORPORATE": "Corps",
            "FINS": "Fins",
            "FINANCIALS": "Fins",
            "FINANCIAL": "Fins",
            "MBS": "MBS",
            "RATES": "Rates",
            "GOVERNMENT": "Rates",
            "TREASURIES": "Rates",
            "EM": "EM",
            "EMERGING": "EM",
            "MUNIS": "Munis",
            "MUNICIPAL": "Munis",
            "ABS": "ABS",
            "CMBS": "CMBS",
            "CLO": "CLO",
            "SOVS": "Sovs",
            "SOVEREIGN": "Sovs",
        }

        if "Sector_L1" in df.columns:
            df["Sector_L1"] = df["Sector_L1"].str.upper().map(
                lambda x: sector_map.get(x, x.title())
            )

        return df

    def _enrich_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Add derived columns for analysis.

        Creates:
        - Liquidity_Proxy: Score based on nominal size
        - Net_Carry: Yield - FTP
        - Carry_Efficiency: Net_Carry / Duration
        - Is_Tradeable: Boolean based on accounting
        """
        # Liquidity Proxy
        df["Liquidity_Proxy"] = np.where(
            df["Nominal_USD"] > LIQUIDITY_THRESHOLD,
            LIQUIDITY_HIGH,
            LIQUIDITY_LOW,
        )

        # Net Carry (in basis points equivalent)
        df["Net_Carry"] = df["Yield"] - df["FTP"]

        # Carry Efficiency (handle division by zero)
        df["Carry_Efficiency"] = np.where(
            df["Duration"] != 0,
            df["Net_Carry"] / df["Duration"],
            np.nan,
        )

        # Is Tradeable flag
        df["Is_Tradeable"] = ~df["Accounting"].isin(NON_TRADEABLE_ACCOUNTING)

        return df

    def _final_cleanup(self, df: pd.DataFrame) -> pd.DataFrame:
        """Final cleanup: drop rows with critical missing data."""
        critical_cols = ["Nominal_USD", "Duration", "Yield"]

        initial_count = len(df)
        df = df.dropna(subset=critical_cols)

        dropped = initial_count - len(df)
        if dropped > 0:
            logger.warning(
                f"Dropped {dropped} rows with missing critical data "
                f"(Nominal, Duration, or Yield)"
            )

        # Reset index
        df = df.reset_index(drop=True)

        return df

    def to_summary(self) -> dict:
        """Generate portfolio summary statistics."""
        if self._clean_df is None:
            return {}

        df = self._clean_df

        return {
            "Total Holdings": len(df),
            "Total AUM (USD)": df["Nominal_USD"].sum(),
            "Weighted Avg Duration": (
                (df["Duration"] * df["Nominal_USD"]).sum() / df["Nominal_USD"].sum()
            ),
            "Weighted Avg Yield": (
                (df["Yield"] * df["Nominal_USD"]).sum() / df["Nominal_USD"].sum()
            ),
            "HTM Holdings": (df["Accounting"] == "HTM").sum(),
            "AFS Holdings": (df["Accounting"] == "AFS").sum(),
            "Sectors": df["Sector_L1"].nunique(),
            "Negative Carry Count": (df["Net_Carry"] < 0).sum(),
        }
