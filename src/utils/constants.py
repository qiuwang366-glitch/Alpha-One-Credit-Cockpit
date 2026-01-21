"""
Constants and configuration for Alpha-One Credit Cockpit.
"""

# Column mapping from bilingual source to standardized names
COLUMN_MAPPING = {
    "分类1": "Sector_L1",
    "分类2": "Sector_L2",
    "TICKER": "Ticker",
    "债券名称": "Name",
    "AccSection": "Accounting",
    "Nominal（USD）": "Nominal_USD",
    "Duration": "Duration",
    "EffectiveYield": "Yield",
    "OAS": "OAS",
    "FTP Rate": "FTP",
}

# Reverse mapping for validation
REVERSE_COLUMN_MAPPING = {v: k for k, v in COLUMN_MAPPING.items()}

# Required columns after transformation
REQUIRED_COLUMNS = [
    "Sector_L1",
    "Ticker",
    "Accounting",
    "Nominal_USD",
    "Duration",
    "Yield",
]

# Sector color palette for visualization
SECTOR_COLORS = {
    "MBS": "#1f77b4",      # Blue
    "Corps": "#ff7f0e",     # Orange
    "Fins": "#2ca02c",      # Green
    "Rates": "#d62728",     # Red
    "EM": "#9467bd",        # Purple
    "Munis": "#8c564b",     # Brown
    "ABS": "#e377c2",       # Pink
    "CMBS": "#7f7f7f",      # Gray
    "CLO": "#bcbd22",       # Yellow-green
    "Sovs": "#17becf",      # Cyan
}

# Default FTP rate for missing values
DEFAULT_FTP = 0.0

# Liquidity score thresholds (in USD millions)
LIQUIDITY_THRESHOLD = 10_000_000  # $10M threshold
LIQUIDITY_HIGH = 5
LIQUIDITY_LOW = 3

# Z-Score thresholds for Rich/Cheap classification
Z_SCORE_THRESHOLDS = {
    "very_rich": -2.0,      # Very expensive
    "rich": -1.5,           # Expensive (sell candidate)
    "neutral_low": -0.5,
    "neutral_high": 0.5,
    "cheap": 1.5,           # Cheap (buy candidate)
    "very_cheap": 2.0,      # Very cheap
}

# Accounting classifications
ACCOUNTING_HTM = "HTM"      # Hold-to-Maturity (not tradeable)
ACCOUNTING_AFS = "AFS"      # Available-for-Sale (tradeable)
ACCOUNTING_FV = "Fair Value"  # Fair Value (tradeable)

NON_TRADEABLE_ACCOUNTING = [ACCOUNTING_HTM]

# Regression parameters
MIN_SAMPLES_FOR_REGRESSION = 5  # Minimum bonds per sector for curve fitting

# Dashboard defaults
DEFAULT_MIN_LIQUIDITY = 1
DEFAULT_EXCLUDE_HTM = True
