# Alpha-One Credit Cockpit

A Python-based Fixed Income Portfolio Analysis System built with Streamlit for quantitative portfolio management.

## Overview

Alpha-One Credit Cockpit is designed for Portfolio Managers managing large Fixed Income portfolios ($50B+). The system digitizes the investment workflow by providing:

- **Rich/Cheap Bond Identification**: Stratified regression analysis with both Quadratic and Nelson-Siegel curve models
- **Single Security Drill-Down**: Interactive ticker inspector with issuer curve visualization
- **Net Carry Efficiency Monitoring**: Track yield vs. funding cost (FTP) to identify "bleeding" assets
- **Valuation Lag Risk Detection**: Highlight positions with potential valuation concerns
- **Accounting-Aware Analysis**: Proper handling of HTM vs. AFS classifications
- **Mobile-First Design**: Responsive dark theme optimized for all devices

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
- Dual-model curve fitting (Quadratic & Nelson-Siegel)
- Rich/Cheap identification via Z-scores
- Net Carry efficiency analysis
- Single security inspector with issuer grouping
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

# Initialize with cleaned data and select model
analyzer = PortfolioAnalyzer(df, model_type="nelson_siegel")  # or "quadratic"

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

### Dual Curve Models

The system supports two yield curve models:

#### 1. Quadratic Model (Polynomial Regression)

For each sector, fits a quadratic yield-duration curve:

$$Yield = a \cdot Duration^2 + b \cdot Duration + c$$

**Advantages:**
- Simple and interpretable
- Fast computation
- Good for standard yield curves

#### 2. Nelson-Siegel Model (Advanced Parametric)

Implements the Nelson-Siegel parametric model:

$$Yield(\tau) = \beta_0 + \beta_1 \cdot \frac{1-e^{-\tau/\lambda}}{\tau/\lambda} + \beta_2 \cdot \left(\frac{1-e^{-\tau/\lambda}}{\tau/\lambda} - e^{-\tau/\lambda}\right)$$

**Parameters:**
- **β₀ (Long-Term Level)**: Asymptotic yield as duration → ∞
- **β₁ (Short-Term Component)**: Slope at the origin (short-term factor)
- **β₂ (Curvature)**: Medium-term curvature component
- **λ (Decay Parameter)**: Controls where the curvature peaks

**Advantages:**
- Theoretically grounded in term structure models
- Better captures non-linear curve shapes
- Separate interpretation of short, medium, and long-term factors
- More robust for irregular yield curves

### Stratified Regression & Z-Scores

**Key Metrics:**
- **Model Yield**: Predicted yield from fitted curve
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

### Tab 1: The Matrix (Relative Value)
- Interactive scatter plot of Duration vs. Yield
- Sector-specific regression curves overlay (Quadratic or Nelson-Siegel)
- Model parameter display panel
- Selected ticker highlighting with gold star marker
- **🔍 Single Security Analysis**:
  - Dropdown selector for any bond ticker
  - Current metrics display (YTM, OAS, Z-Score)
  - Scenario analysis table (Actual vs Fair Yield)
  - Automated trading recommendations
  - Issuer curve visualization showing all bonds from same issuer
- Hover tooltips with bilingual bond details

### Tab 2: Optimization Lab
- Sell Candidates table (Z-Score < -1.5)
- Bleeding Assets table (Net Carry < 0)
- Carry efficiency distribution
- Position exposure summaries

### Tab 3: Issuer 360 Dashboard
- **Issuer Selection**: Dropdown to select any issuer from the portfolio with quick stats
- **Section A - Valuation Curve**:
  - Scatter plot of issuer's bonds (gold diamonds) overlaid on sector curve
  - Issuer-specific curve interpolation (if 3+ bonds available)
  - Sector benchmark curve (Nelson-Siegel) for comparison
  - Visual insight: trading Wide (Rich) or Tight (Cheap) vs. sector
- **Section B - Financial Dashboard**:
  - 2x2 grid of quarterly trend charts (8 quarters)
  - Deleveraging: Bar chart (Total Liabilities) + Line (Net Leverage)
  - Liquidity: Stacked area (Cash vs. Net Interest Expense)
  - Profitability: Line chart (EBITDA Margin)
  - Growth: Bar chart (Revenue QoQ)
- **Section C - Credit Peers**:
  - Radar chart comparing issuer vs. sector average
  - Metrics: Net Leverage (Inverse), Interest Coverage, EBITDA Margin, Cash Ratio, Revenue Growth
  - Automated insights and peer statistics
  - Fallback to side-by-side bar chart if radar chart fails

### Tab 4: Management Brief
- One-click executive summary generation
- Portfolio metrics overview
- Sector allocation visualization
- Data export functionality (Full Portfolio, Sell List, Regression Stats)

### Features
- **📱 Mobile-First Design**: Responsive layout optimized for all screen sizes
- **🌓 Dark Theme**: Professional Bloomberg/Aladdin-style institutional UI
- **🌐 Bilingual Interface**: All labels in English/Chinese (英文/中文)
- **🔬 Model Selection**: Toggle between Quadratic and Nelson-Siegel models
- **⭐ Ticker Highlighting**: Selected bonds shown as gold stars on main chart
- **🏢 Issuer Grouping**: Automatic detection and visualization of bonds from same issuer

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

---

## Development Changelog

### 2026-01-22 (Phase 2: Advanced Modeling & Interactivity)

**Nelson-Siegel Model Implementation**
- Added Nelson-Siegel parametric yield curve model as an alternative to quadratic regression
- Implemented `nelson_siegel()` function with β₀, β₁, β₂, λ parameters
- Added `NelsonSiegelResult` dataclass for storing fitted parameters
- Used `scipy.optimize.curve_fit` for parameter calibration with proper bounds
- Model selection toggle in UI (Quadratic vs Nelson-Siegel)
- Display model-specific parameters in statistics panel

**Single Security Analysis**
- Interactive ticker dropdown selector (alphabetically sorted)
- Selected ticker highlighted as gold star ⭐ on main scatter plot
- Current metrics cards: YTM, OAS, Z-Score with color coding
- Scenario analysis table: Actual Yield, Fair Yield, Residual, Z-Score
- Automated interpretation: Rich/Cheap/Fair with buy/sell/hold recommendations
- Smart issuer detection and grouping

**Issuer Curve Visualization**
- Automatic detection of bonds from same issuer
- Mini-chart showing issuer-specific yield curve
- Sector curve overlay for reference
- Gold star highlighting for selected bond
- Shows count of sibling bonds found

**Technical Improvements**
- Added `importlib.reload()` to force latest module versions and prevent cache issues
- Created comprehensive `.gitignore` for Python cache files
- Robust error handling for curve fitting with small datasets
- All Z-score calculations unified for both model types
- Maintained backward compatibility with quadratic model

**Commits:**
- `34304da` - Fix module reload issue: Add importlib.reload() to force latest module versions
- `8e65ffd` - Add .gitignore to exclude Python cache files and temporary artifacts
- `c6c0783` - Implement Nelson-Siegel model and single security drill-down analysis

### 2026-01-22 (Phase 1.5: UI/UX Enhancement)

**Mobile-First Redesign**
- Complete UI overhaul with Bloomberg/Aladdin-style dark theme
- Responsive design optimized for mobile devices
- Custom CSS with glassmorphism effects and smooth animations
- Collapsible filters with mobile-friendly touch targets

**Bilingual Interface**
- Full Chinese/English dual language support
- All labels, tooltips, and help text in both languages
- Chinese sector name translations
- Bilingual metric cards and data tables

**Visual Improvements**
- Professional color palette (dark blues, purples, greens)
- Smooth gradient backgrounds
- Custom scrollbars matching theme
- Hover effects and transitions
- Metric cards with accent borders
- Bond cards for mobile view

**Bug Fixes**
- Fixed Plotly layout TypeError by replacing dict unpacking with helper function
- Improved error handling for missing data

**Commits:**
- `c45e8f1` - Fix Plotly layout TypeError by replacing dict unpacking with helper function
- `605b114` - Upgrade to institutional-grade mobile-first bilingual dashboard

### 2026-01-21 (Phase 1: MVP Launch)

**Core System Implementation**
- Complete architecture setup with modular structure
- Data loader with bilingual CSV parsing
- Quadratic regression for yield curve fitting
- Z-score based Rich/Cheap identification
- Net Carry efficiency analysis

**Analytics Engine**
- `PortfolioAnalyzer` class with stratified regression
- Automatic sector curve fitting
- Sell candidates identification (Z < -1.5)
- Bleeding assets detection (Net Carry < 0)
- Portfolio metrics aggregation
- Executive summary generation

**Dashboard Features**
- Three-tab interface: Matrix / Optimization Lab / Management Brief
- Interactive Duration-Yield scatter plots
- Sector-specific regression curves overlay
- Carry distribution histogram
- Sector allocation pie chart
- CSV data export functionality

**Data Processing**
- Robust CSV parsing with column mapping
- Data validation and quality reporting
- Derived metrics calculation (Net Carry, Carry Efficiency)
- Liquidity proxy scoring
- Accounting classification handling

**Technical Foundation**
- Abstract base classes for future LLM integration (Module A)
- Unit tests framework
- Type hints and documentation
- Constants management
- Error handling and logging

**Commits:**
- `92fe061` - Implement Alpha-One Credit Cockpit fixed income portfolio system
- `bac31be` - Merge pull request #1
- `dff66b9` - Initial repository setup

### 2026-01-23 (Phase 3: Fundamental Integration & UI Polish)

**Financial Fundamentals Module**
- Created `src/module_b/financials.py` for quarterly financial data processing
- Implemented `FinancialDataLoader` class with automatic bond-to-equity ticker mapping
- Added `QuarterlyMetrics` and `IssuerFundamentals` dataclasses for structured data
- Metric calculations: Net Debt Proxy, Net Leverage, Interest Coverage, Revenue QoQ Growth
- Graceful handling of missing EBITDA/Interest Expense (fill with 0 or exclude)
- 8-quarter historical data caching for trend analysis

**Bloomberg Terminal Aesthetic**
- Updated CSS color scheme: Deep Dark (#121212), Bloomberg Orange (#FF9800), Terminal Blue (#00B0FF)
- Added monospace fonts (Roboto Mono) for financial metrics
- Enhanced metric cards with orange accent borders
- Professional glassmorphism effects with backdrop blur
- Custom styling for fundamental panels and KPI cards

**Language Toggle**
- Added bilingual toggle button (🌐 EN/CN) in header
- Session state management for language preference
- Button with hover effects and active state styling
- Seamless language switching with page rerun

**Credit Inspector Panel**
- Integrated fundamentals display directly on main page (Tab 1)
- Two-column layout: LEFT (Pricing Analysis), RIGHT (Financial Fundamentals)
- LEFT column shows Fair Value and Z-Score valuation metrics
- RIGHT column displays:
  - Issuer information (Equity Ticker & Name)
  - Three KPI cards: Revenue Growth QoQ, Net Leverage, Interest Coverage
  - 8-quarter trend chart for Net Leverage (area chart, minimalist design)
- Color-coded metrics: Green (safe), Yellow (moderate), Red (at risk)
- Automatic mapping via `bond_equity_map.csv` and `quarterly_financials.csv`

**Data Architecture**
- Loaded `bond_equity_map.csv` (131 issuers) with Bond_Ticker → Equity_Ticker mapping
- Loaded `quarterly_financials.csv` with historical quarterly data
- Automatic data loading on app startup with coverage statistics
- Graceful fallback if fundamental data not available for specific bonds

**Technical Improvements**
- Added module reload for `financials.py` to prevent cache issues
- Session state management for financial data loader
- Efficient caching of issuer fundamentals with O(1) lookup by bond ticker
- Robust error handling for missing or incomplete fundamental data
- Automatic sorting of quarterly data by date ascending

**User Experience**
- Credit Inspector appears below Single Security Analysis when ticker selected
- Trend chart uses clean design with no grid lines (Bloomberg style)
- Hover tooltips show quarter and exact leverage values
- Issuer equity ticker displayed with orange highlight
- Seamless integration with existing pricing analytics

**Commits:**
- TBD - Phase 3: Integrate financial fundamentals with Credit Inspector panel

### 2026-01-23 (Phase 3.5: Issuer 360 Dashboard)

**Comprehensive Issuer Deep Dive**
- Created new Tab 3 "Issuer 360 / 发行人全景" dedicated to single issuer analysis
- Moved Executive Brief to Tab 4 to accommodate new dashboard
- Issuer dropdown selector with real-time quick stats (bond count, total exposure)
- Dynamic filtering to show only issuers with bonds in current portfolio

**Section A: Valuation Curve (Issuer vs. Sector)**
- Scatter plot with issuer's bonds as gold diamond markers
- Issuer-specific yield curve interpolation (linear) for 3+ bonds
- Sector benchmark curve (Nelson-Siegel) overlaid for comparison
- Visual insight panel: identifies if issuer is trading Wide/Tight vs. sector
- Avg Z-Score calculation across all issuer bonds with color-coded signals
- Quick metrics: weighted duration, weighted YTM, bond count

**Section B: Financial Dashboard (2x2 Grid)**
- Quarterly trend analysis using last 8 quarters of financial data
- Chart 1 - Deleveraging: Dual-axis chart with Total Liabilities (bars, left) + Net Leverage (line, right)
- Chart 2 - Liquidity: Stacked area showing Cash vs. Net Interest Expense
- Chart 3 - Profitability: Line chart with fill showing EBITDA Margin trend
- Chart 4 - Growth: Color-coded bar chart (green/red) for Revenue QoQ Growth
- All charts use Bloomberg-style minimalist design with dark theme

**Section C: Credit Peers Comparison**
- Automated peer group identification based on issuer's sector
- Calculation of sector averages for latest quarter across 5 key metrics
- Radar chart (spider chart) comparing issuer vs. sector average:
  - Net Leverage (Inverted for better visual interpretation)
  - Interest Coverage
  - EBITDA Margin
  - Cash Ratio
  - Revenue Growth
- Fallback to side-by-side comparison table if radar chart fails
- Automated insights generation: identifies strengths/weaknesses vs. peers
- Peer statistics panel: sector name, peer count, key takeaways

**Technical Implementation**
- Integration with `FinancialDataLoader` for quarterly metrics
- Efficient use of issuer fundamentals cache built at app startup
- Robust error handling for missing financial data
- Graceful degradation when peer data unavailable
- Uses `scipy.interpolate.interp1d` for issuer curve fitting
- Color-coded insights using conditional logic on metric comparisons
- Responsive 2-column layouts throughout for desktop/mobile

**User Experience**
- Clear visual hierarchy with three distinct sections
- All text bilingual (English/Chinese) throughout
- Tooltips and hover states for all interactive elements
- Empty state messages when issuer has no bonds or data
- Seamless integration with existing portfolio filters
- Professional Bloomberg-style dark theme maintained

**Commits:**
- TBD - Phase 3.5: Implement Issuer 360 comprehensive dashboard

---

**Total Development Time**: 4 days
**Current Version**: 3.5 (Phase 3.5)
**Lines of Code**: ~5,500
**Test Coverage**: In Progress
