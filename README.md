# Alpha-One Credit Cockpit

A Python-based Fixed Income Portfolio Analysis System built with Streamlit for quantitative portfolio management.

## Overview

Alpha-One Credit Cockpit is designed for Portfolio Managers managing large Fixed Income portfolios ($50B+). The system digitizes the investment workflow by providing:

- **Rich/Cheap Bond Identification**: Stratified regression analysis to identify bonds trading expensive or cheap relative to their sector curves
- **Net Carry Efficiency Monitoring**: Track yield vs. funding cost (FTP) to identify "bleeding" assets
- **Valuation Lag Risk Detection**: Highlight positions with potential valuation concerns
- **Accounting-Aware Analysis**: Proper handling of HTM vs. AFS classifications

## Architecture

```
Alpha-One-Credit-Cockpit/
├── app.py                      # Streamlit dashboard (entry point)
├── requirements.txt            # Python dependencies
├── data/
│   └── portfolio.csv           # Sample portfolio data
├── src/
│   ├── __init__.py
│   ├── module_a/               # Issuer 360 (Future: AI Qualitative Analysis)
│   │   ├── __init__.py
│   │   ├── base.py             # Abstract Base Classes for LLM integration
│   │   └── issuer_360.py       # Main engine (placeholder)
│   ├── module_b/               # Portfolio Optimizer (MVP)
│   │   ├── __init__.py
│   │   ├── data_loader.py      # Data cleaning & transformation
│   │   └── analytics.py        # Quantitative analysis engine
│   └── utils/
│       ├── __init__.py
│       └── constants.py        # Configuration constants
└── tests/                      # Unit tests
```

### Module A: Issuer 360 (Future Expansion)

AI-driven qualitative analysis module. Currently provides:
- Abstract Base Classes for future LLM integration
- Placeholder implementations for credit profiling, document processing, and news analysis
- Designed for seamless integration with OpenAI, Anthropic, or other LLM providers

### Module B: Portfolio Optimizer (Current MVP)

Quantitative scanning of current holdings with:
- Stratified regression for Rich/Cheap identification
- Net Carry efficiency analysis
- Sector-specific yield curve fitting
- Accounting classification handling (HTM/AFS)

## Installation

```bash
# Clone the repository
git clone <repository-url>
cd Alpha-One-Credit-Cockpit

# Create virtual environment (recommended)
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

## Usage

### Running the Dashboard

```bash
streamlit run app.py
```

The dashboard will open in your browser at `http://localhost:8501`.

### Using the Data Loader

```python
from src.module_b.data_loader import DataLoader

# Load and clean portfolio data
loader = DataLoader()
df = loader.load("path/to/portfolio.csv")

# Check data quality
report = loader.get_quality_report()
print(report.to_dict())
```

### Using the Analytics Engine

```python
from src.module_b.analytics import PortfolioAnalyzer

# Initialize with cleaned data
analyzer = PortfolioAnalyzer(df)

# Fit sector curves
regression_results = analyzer.fit_sector_curves()

# Get sell candidates (rich bonds)
sell_candidates = analyzer.get_sell_candidates(z_threshold=-1.5)

# Get bleeding assets (negative carry)
bleeding = analyzer.get_bleeding_assets()

# Generate executive summary
summary = analyzer.generate_executive_summary()
```

## Data Format

The system accepts CSV files with bilingual (Chinese/English) columns:

| Source Column | Target Column | Description |
|---------------|---------------|-------------|
| 分类1 | Sector_L1 | Primary sector (MBS, Corps, Fins, etc.) |
| 分类2 | Sector_L2 | Sub-sector (SOE, Foreign Banks, etc.) |
| TICKER | Ticker | Bond ticker symbol |
| 债券名称 | Name | Bond name |
| AccSection | Accounting | Accounting classification (HTM, AFS, Fair Value) |
| Nominal（USD） | Nominal_USD | Position size in USD |
| Duration | Duration | Modified duration |
| EffectiveYield | Yield | Effective yield (cleaned to decimal) |
| OAS | OAS | Option-Adjusted Spread |
| FTP Rate | FTP | Funding Transfer Price |

### Derived Columns (Auto-Generated)

| Column | Formula | Description |
|--------|---------|-------------|
| Liquidity_Proxy | If Nominal > $10M: 5, else: 3 | Liquidity score |
| Net_Carry | Yield - FTP | Carry after funding |
| Carry_Efficiency | Net_Carry / Duration | Carry per unit duration |
| Is_Tradeable | Accounting != 'HTM' | Can be sold |

## Quantitative Methodology

### Stratified Regression

For each sector, the system fits a quadratic yield-duration curve:

$$Yield = a \cdot Duration^2 + b \cdot Duration + c$$

**Key Metrics:**
- **Residual**: Actual Yield - Model Yield
- **Z-Score**: Residual / Standard Deviation of Residuals

**Interpretation:**
- Z-Score < -1.5: **Rich** (expensive, sell candidate)
- Z-Score > +1.5: **Cheap** (attractive, buy candidate)
- -0.5 < Z-Score < +0.5: **Fair Value**

### Accounting Constraints

- **HTM (Hold-to-Maturity)**: Cannot be sold due to regulatory requirements. Excluded from optimization suggestions.
- **AFS (Available-for-Sale)**: Can be traded freely.
- **Fair Value**: Marked to market, tradeable.

## Dashboard Features

### Tab 1: The Matrix
- Interactive scatter plot of Duration vs. Yield
- Sector-specific regression curves overlay
- Hover tooltips with bond details

### Tab 2: Optimization Lab
- Sell Candidates table (Z-Score < -1.5)
- Bleeding Assets table (Net Carry < 0)
- Carry efficiency distribution

### Tab 3: Management Brief
- One-click executive summary generation
- Portfolio metrics overview
- Sector allocation visualization
- Data export functionality

## Future Development

### Module A Integration
The abstract base classes in `src/module_a/base.py` are designed for:
- **BaseCreditProfiler**: LLM-powered credit profile generation
- **BaseDocumentProcessor**: SEC filing and covenant document analysis
- **BaseNewsAnalyzer**: News sentiment and material event detection

To integrate an LLM provider:

```python
from src.module_a.base import BaseCreditProfiler
from src.module_a.issuer_360 import Issuer360Engine

# Implement your custom profiler
class OpenAICreditProfiler(BaseCreditProfiler):
    def generate_profile(self, issuer_id, ...):
        # Your LLM implementation
        pass

# Register with the engine
engine = Issuer360Engine()
engine.register_credit_profiler(OpenAICreditProfiler())
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Write tests for new functionality
4. Submit a pull request

## License

MIT License

## Contact

For questions or support, please open an issue in the repository.
