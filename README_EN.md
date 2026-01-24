# 🚀 Alpha-One Credit Cockpit

> **Redefining Fixed Income Portfolio Management from a Trader's Perspective**
> An institutional-grade quantitative analysis system designed for the real world

[![LinkedIn](https://img.shields.io/badge/LinkedIn-Liu%20Lu-0077B5?style=for-the-badge&logo=linkedin&logoColor=white)](https://www.linkedin.com/in/liulu-math/)
[![Made with Python](https://img.shields.io/badge/Made%20with-Python-1f425f.svg?style=for-the-badge)](https://www.python.org/)
[![Streamlit](https://img.shields.io/badge/Streamlit-FF4B4B?style=for-the-badge&logo=Streamlit&logoColor=white)](https://streamlit.io)

[中文版](./README.md) | English Version

---

## 💡 Project Origin: From Pain Points to Solutions

When managing a fixed income portfolio of over **$50 billion**, portfolio managers face these core challenges daily:

- 📊 **Relative Value Discovery**: Among hundreds of bonds, which are **Rich** (overvalued) and which are **Cheap** (undervalued)?
- 💰 **Funding Cost Management**: After accounting for funding costs (FTP), which assets are "**bleeding**" (negative carry)?
- 📈 **Fundamental Integration**: How to seamlessly combine pricing analysis with issuer financial health?
- 🔍 **Single Security Deep Dive**: How to quickly view a single bond's **fair value**, **same-issuer comparison**, and **financial trends**?
- 🏢 **Issuer 360 View**: How to systematically assess an issuer's **valuation deviation**, **financial health**, and **peer benchmarking**?

**Alpha-One Credit Cockpit** is a tool built specifically to address these real trading scenarios — it's not an academic project, but an analysis system **ready for production deployment**.

---

## ✨ Core Value Proposition

### 1. 🎯 Statistics-Driven Relative Value Analysis

Traditional approaches rely on experience and intuition, while this system uses **stratified regression** and **Z-Score standardization** to make rich/cheap judgments evidence-based:

```
Dual-Model Architecture:
├─ Quadratic Model (Polynomial)     → Simple, fast, suitable for standard curves
└─ Nelson-Siegel Model (Parametric) → Theoretically rigorous, suitable for complex curves

Stratified Strategy:
Group by sector → Fit sector-specific yield curves → Calculate residual Z-Scores → Identify trading opportunities

Z-Score Interpretation:
• Z < -1.5  →  Rich        → Sell candidate
• Z > +1.5  →  Cheap       → Buy candidate
• |Z| < 0.5 →  Fair Value  → Hold
```

### 2. 💸 Funding Cost Awareness (Net Carry Analysis)

Many bonds appear attractive on the surface, but may be **negative contributors** after deducting funding costs (FTP):

```python
Net_Carry = Yield - FTP
Carry_Efficiency = Net_Carry / Duration  # Net spread per unit duration

# System automatically identifies "Bleeding Assets"
bleeding_assets = portfolio[portfolio['Net_Carry'] < 0]
```

This allows portfolio managers to **quantify each position's contribution to overall profitability**, not just nominal yields.

### 3. 🏢 Issuer 360° Panoramic Analysis

Innovatively integrates **pricing analysis** with **financial fundamentals** in a single view:

**A. Valuation Curve Comparison**
- Issuer bonds' position on sector curve (rich or cheap?)
- Issuer-specific curve fitting (for 3+ bonds)
- Average Z-Score calculation

**B. Financial Dashboard (8-Quarter Trends)**
- Deleveraging progress (Total Debt + Net Leverage)
- Liquidity status (Cash vs Interest Expense)
- Profitability (EBITDA Margin)
- Growth momentum (Revenue QoQ Growth)

**C. Peer Benchmarking (Radar Chart)**
- 5-dimensional comparison: Net Leverage, Interest Coverage, EBITDA Margin, Cash Ratio, Revenue Growth
- Automatically identifies issuer's **strengths** and **weaknesses** relative to industry

### 4. 📱 Institutional-Grade User Experience

- **Mobile-First Design**: Responsive layout, supports tablets/phones for on-the-go viewing
- **Bloomberg Terminal Aesthetics**: Professional dark theme (`#121212` background + `#FF9800` accent)
- **Bilingual Interface**: All labels and tooltips in **English and Chinese**
- **Real-Time Interaction**: Plotly charts support zooming, hovering, drill-down

### 5. 🤖 Extension Framework for the AI Era

**Module A** provides complete abstract base classes, ready for future integration of LLMs (GPT-4, Claude, etc.):

```python
# Three abstract interfaces
BaseCreditProfiler       # AI-driven credit profile generation
BaseDocumentProcessor    # SEC filing and covenant document analysis
BaseNewsAnalyzer         # News sentiment and material event detection

# Plug-and-play design
from src.module_a.base import BaseCreditProfiler

class GPT4CreditProfiler(BaseCreditProfiler):
    def generate_profile(self, issuer_id):
        # Connect to OpenAI API
        pass

engine.register_credit_profiler(GPT4CreditProfiler())
```

---

## 🎓 Design Philosophy & Technical Insights

### Why Nelson-Siegel Model?

In fixed income analysis, simple polynomial regression (quadratic curves) is fast but has two issues:

1. **Parameters lack economic meaning**: Coefficients a, b, c are just mathematical fitting results
2. **Poor robustness for abnormal curves**: Fits poorly when yield curves invert or hump

The **Nelson-Siegel model** elegantly solves these problems:

```
Yield(τ) = β₀ + β₁·f₁(τ) + β₂·f₂(τ)

Where:
• β₀ (Level)     → Long-term yield level (asymptote)
• β₁ (Slope)     → Short-term factor (initial curve slope)
• β₂ (Curvature) → Medium-term curvature (hump shape)
• λ (Decay)      → Controls where β₂ influence peaks
```

**Each parameter has clear economic meaning**, allowing us to:
- Analyze structural changes in short-, medium-, and long-term rates
- Identify "convexity" and "concavity" characteristics of curves
- Better fit irregularly-shaped yield curves

**Technical Implementation Highlight**: Uses `scipy.optimize.curve_fit` for automatic parameter optimization with reasonable boundary constraints ensuring convergence stability.

### Why Stratified Regression?

Regressing all bonds together can produce **Simpson's Paradox**:

```
Example:
Financial bonds average yield 4.5%, Corporate bonds average 5.5%
If we regress all together, a 5% financial bond appears "cheap"
But actually it may be "rich" within the financial sector
```

**Solution**: Group by `Sector_L1` (primary sector), fit independent curves for each sector

```python
for sector in df['Sector_L1'].unique():
    sector_data = df[df['Sector_L1'] == sector]
    curve_params = fit_curve(sector_data)
    df.loc[sector_data.index, 'Model_Yield'] = predict(curve_params)
    df.loc[sector_data.index, 'Z_Score'] = (Yield - Model_Yield) / std
```

This way each Z-Score is **calculated relative to its sector curve**, eliminating systematic bias across sectors.

### Why Separate Module A/B Architecture?

**Module B (Current MVP)**: Quantitative analysis engine
- Pure numerical computation, no external APIs needed
- Data processing → Curve fitting → Optimization recommendations
- Can run offline

**Module A (Future Extension)**: AI qualitative analysis
- Requires LLM APIs (OpenAI / Anthropic / Local models)
- Credit profile generation, document parsing, news analysis
- Optional module, load on demand

**Design Philosophy**:
1. **Progressive feature enhancement**: Implement core quantitative features first, then layer on AI capabilities
2. **Cost control**: Users not using LLMs don't incur API fees
3. **Interface standardization**: Clear contracts via abstract base classes, any LLM provider can plug in

This design embodies the **Open-Closed Principle** of software engineering: open for extension, closed for modification.

---

## 🏗️ System Architecture

```
Alpha-One-Credit-Cockpit/
│
├── app.py                          # Streamlit main application (Entry Point)
│   ├── Tab 1: Issuer 360
│   │   ├── Valuation Curve Comparison (Issuer vs Sector)
│   │   ├── Financial Dashboard (2x2 Grid)
│   │   └── Peer Benchmarking (Radar Chart)
│   ├── Tab 2: Relative Value Matrix
│   │   ├── Duration-Yield Scatter + Regression Curves
│   │   ├── Single Security Analysis
│   │   └── Credit Inspector
│   ├── Tab 3: Optimization Lab
│   │   ├── Sell Candidates (Rich Bonds)
│   │   ├── Bleeding Assets
│   │   └── Carry Efficiency Distribution
│   └── Tab 4: Executive Brief
│       ├── Portfolio Metrics Overview
│       └── CSV Export (Full/Filtered/Regression Stats)
│
├── src/
│   ├── module_a/                   # AI Qualitative Analysis (Future)
│   │   ├── base.py                 # Abstract base classes (3 interfaces)
│   │   │   ├── BaseCreditProfiler        # Credit profile generation
│   │   │   ├── BaseDocumentProcessor     # Document parsing
│   │   │   └── BaseNewsAnalyzer          # News analysis
│   │   └── issuer_360.py           # Issuer 360 Engine
│   │
│   ├── module_b/                   # Quantitative Analysis (Current MVP)
│   │   ├── data_loader.py          # Data ETL Pipeline
│   │   │   ├── Bilingual column mapping (EN/CN)
│   │   │   ├── Encoding compatibility (UTF-8/GBK/GB2312)
│   │   │   ├── Dirty data cleaning (%, commas, parentheses)
│   │   │   └── Data quality reporting
│   │   │
│   │   ├── analytics.py            # Core Analysis Engine
│   │   │   ├── nelson_siegel() - NS model implementation
│   │   │   ├── quadratic_curve() - Quadratic curve
│   │   │   ├── PortfolioAnalyzer class
│   │   │   │   ├── fit_sector_curves() - Stratified regression
│   │   │   │   ├── get_sell_candidates() - Rich identification
│   │   │   │   ├── get_bleeding_assets() - Negative Carry identification
│   │   │   │   └── generate_executive_summary()
│   │   │   └── Total return analysis (Rolldown effect)
│   │   │
│   │   └── financials.py           # Financial Fundamentals Module
│   │       ├── FinancialDataLoader
│   │       ├── Bond-Equity ticker mapping (131 issuers)
│   │       ├── Quarterly data alignment (8 quarters)
│   │       └── Calculations: Net Leverage, Interest Coverage, QoQ Growth
│   │
│   └── utils/
│       └── constants.py            # Configuration constants (colors, thresholds)
│
├── data/
│   ├── portfolio.csv               # Portfolio holdings data
│   ├── bond_equity_map.csv         # Bond→Equity ticker mapping
│   └── quarterly_financials.csv    # Quarterly financial data
│
└── tests/
    ├── test_data_loader.py
    └── test_analytics.py
```

---

## 🚀 Quick Start

### Installation

```bash
# 1. Clone repository
git clone https://github.com/your-repo/Alpha-One-Credit-Cockpit.git
cd Alpha-One-Credit-Cockpit

# 2. Create virtual environment (Python 3.9+ recommended)
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt
```

### Run

```bash
# Start Streamlit application
streamlit run app.py

# Browser automatically opens http://localhost:8501
```

### Use Your Own Data

Replace `data/portfolio.csv` with your holdings data (must include required columns), then restart the app:

```python
# Required columns (English or Chinese column names accepted)
required_columns = [
    'Sector_L1 / 分类1',        # Primary sector
    'Ticker / TICKER',          # Bond ticker
    'Duration',                 # Modified duration
    'Yield / EffectiveYield',   # Effective yield
    'OAS',                      # Option-adjusted spread
]

# Optional columns (enhanced functionality)
optional_columns = [
    'FTP / FTP Rate',           # Funds Transfer Pricing (for Net Carry calculation)
    'Accounting / AccSection',  # Accounting classification (for tradeability)
    'Nominal_USD / Nominal（USD）',  # Position size (for liquidity score)
]
```

---

## 🧠 About the Author

I'm **Liu Lu**, with dual backgrounds in mathematics and finance, specializing in **quantitative investment** and **machine learning applications in finance**.

**Design Philosophy of This Project**:

1. **Pragmatism**: Not technology for technology's sake, but solving real trading scenario pain points
2. **Modularity**: Module A/B separation, progressive feature enhancement, lowering usage barriers
3. **Engineering Quality**: Data cleaning, error handling, test coverage, ensuring production-grade stability
4. **Extensibility**: Interfaces reserved for AI era, seamless LLM integration in the future

**My Tech Stack**:
- **Quantitative Analysis**: Python (Pandas, NumPy, SciPy), R, MATLAB
- **Machine Learning**: Scikit-learn, XGBoost, TensorFlow/PyTorch
- **Data Engineering**: SQL, Spark, Airflow
- **Web Development**: Streamlit, Flask, React
- **Fixed Income**: Yield curve modeling, credit analysis, risk management

**Contact**:

📧 **LinkedIn**: [https://www.linkedin.com/in/liulu-math/](https://www.linkedin.com/in/liulu-math/)
💼 **Seeking Opportunities**: Quantitative research, data science, financial engineering roles

If you're interested in this project, or have collaboration/job opportunities, feel free to reach out via LinkedIn!

---

## 🛠️ Tech Stack

| Category | Technology | Version | Purpose |
|---------|-----------|---------|---------|
| **Language** | Python | 3.9+ | Core development language |
| **UI Framework** | Streamlit | 1.28+ | Rapid web app development |
| **Data Processing** | Pandas | 2.0+ | DataFrame operations, ETL |
| **Numerical Computing** | NumPy | 1.24+ | Matrix operations, math functions |
| **Scientific Computing** | SciPy | 1.10+ | Curve fitting, optimization algorithms |
| **Visualization** | Plotly | 5.18+ | Interactive charts |
| **Testing** | Pytest | 7.4+ | Unit testing |
| **Type Checking** | mypy | 1.5+ | Static type checking (optional) |

---

## 📄 Open Source License

This project is licensed under the **MIT License**, allowing you to freely:

- ✅ Commercial use
- ✅ Modify code
- ✅ Distribute copies
- ✅ Private use

**Only requirement**: Retain original author's copyright notice.

See [LICENSE](LICENSE) file for details.

---

## 🙏 Acknowledgments

Thanks to the following open source projects and tools:

- **Streamlit**: Enabling Python developers to rapidly build beautiful web apps
- **Plotly**: Powerful library for interactive charts
- **Pandas**: Swiss Army knife of data analysis
- **SciPy**: Foundation of scientific computing
- **Nelson-Siegel Model**: Thanks to Charles Nelson and Andrew Siegel for pioneering research

And all developers who provided feedback and suggestions on GitHub!

---

## 📮 Contact & Feedback

If you have any questions, suggestions, or collaboration intentions, feel free to contact me:

- 📧 **LinkedIn**: [Liu Lu's LinkedIn Profile](https://www.linkedin.com/in/liulu-math/)
- 🐛 **Bug Reports**: [GitHub Issues](https://github.com/your-repo/Alpha-One-Credit-Cockpit/issues)
- 💡 **Feature Requests**: [GitHub Discussions](https://github.com/your-repo/Alpha-One-Credit-Cockpit/discussions)

**If this project helps you, please give it a ⭐Star! That's the greatest encouragement for me!**

---

## 📚 Development Log

> Detailed development history showing the project's iteration from 0 to 1.

---

## 2026-01-23 (Phase 3.5: Issuer 360 Dashboard)

### 🎯 Comprehensive Issuer Deep Dive

**New Tab 3: Issuer 360**
- Created dedicated issuer deep-dive tab
- Moved original Executive Brief to Tab 4
- Issuer dropdown selector with real-time quick stats (bond count, total exposure)
- Dynamic filtering to show only issuers with bonds in current portfolio

**Section A: Valuation Curve (Issuer vs Sector)**
- Scatter plot: Issuer bonds marked with gold diamonds
- Issuer-specific curve interpolation (linear, for 3+ bonds)
- Overlay sector benchmark curve (Nelson-Siegel) for comparison
- Visual insights panel: identifies if issuer trades rich/cheap vs sector
- Calculates average Z-Score across all issuer bonds with color-coded signal
- Quick metrics: weighted duration, weighted YTM, bond count

**Section B: Financial Dashboard (2x2 Grid)**
- Trend analysis using last 8 quarters of financial data
- **Chart 1 - Deleveraging**: Dual-axis with Total Debt (bars) + Net Leverage (line)
- **Chart 2 - Liquidity**: Stacked area chart, Cash vs Net Interest Expense
- **Chart 3 - Profitability**: Line chart with fill, EBITDA Margin trend
- **Chart 4 - Growth**: Color-coded bars (green/red), Revenue QoQ Growth
- All charts use Bloomberg-style minimalist design and dark theme

**Section C: Credit Peer Comparison**
- Automatically identifies peer group based on issuer's sector
- Calculates sector averages for latest quarter across 5 key metrics
- **Radar Chart (Spider Plot)** comparing issuer vs sector average:
  - Net Leverage (inverted for visual clarity)
  - Interest Coverage
  - EBITDA Margin
  - Cash Ratio
  - Revenue Growth
- Graceful degradation to side-by-side comparison table if radar fails
- Automated insight generation: identifies strengths/weaknesses vs peers
- Peer stats panel: sector name, peer count, key takeaways

### 🔧 Technical Implementation

- Integration with `FinancialDataLoader` for quarterly metrics
- Efficient use of issuer fundamentals cache built at app startup
- Robust error handling for missing financial data
- Graceful degradation when peer data unavailable
- Uses `scipy.interpolate.interp1d` for issuer curve fitting
- Color-coded insights using conditional logic for metric comparisons
- Responsive 2-column layout throughout for desktop/mobile

### 💎 User Experience

- Clear visual hierarchy across three distinct sections
- Bilingual throughout (English/Chinese)
- Tooltips and hover states for all interactive elements
- Empty state messages when issuer has no bonds or data
- Seamless integration with existing portfolio filters
- Maintains professional Bloomberg-style dark theme

---

## 2026-01-23 (Phase 3: Fundamental Integration & UI Polish)

### 💰 Financial Fundamentals Module

**Created `src/module_b/financials.py`**
- Implemented `FinancialDataLoader` class with automatic bond-equity ticker mapping
- Added `QuarterlyMetrics` and `IssuerFundamentals` data classes
- Metric calculations:
  - Net Debt proxy (Total Liabilities - Cash)
  - Net Leverage (Net Debt / EBITDA)
  - Interest Coverage (EBITDA / Interest Expense)
  - Revenue QoQ Growth
- Graceful handling of missing EBITDA/interest expense (fill 0 or exclude)
- 8-quarter historical data caching for trend analysis

### 🎨 Bloomberg Terminal Aesthetics

**Updated CSS Color Scheme**
- Deep black background: `#121212`
- Bloomberg orange accent: `#FF9800`
- Terminal blue: `#00B0FF`
- Monospace font (Roboto Mono) for financial metrics
- Enhanced metric cards with orange accent borders
- Professional glassmorphism effects with backdrop blur
- Custom styling for fundamentals panels and KPI cards

### 🌐 Language Toggle

- Added bilingual toggle button in header (🌐 EN/CN)
- Session state management for language preference
- Button with hover effects and active state styling
- Seamless language switching via page rerun

---

## 2026-01-22 (Phase 2: Advanced Modeling & Interactivity)

### 📐 Nelson-Siegel Model Implementation

**Mathematical Model**
- Implemented Nelson-Siegel parametric yield curve model
- Four parameters: β₀ (long-term level), β₁ (short-term factor), β₂ (curvature), λ (decay)
- Added `NelsonSiegelResult` dataclass to store fitted parameters
- Uses `scipy.optimize.curve_fit` for parameter calibration with reasonable bounds

**UI Integration**
- Model selection toggle: Quadratic vs Nelson-Siegel
- Stats panel displays model-specific parameters
- Unified Z-Score calculation supporting both models
- Maintains backward compatibility with quadratic model

### 🔍 Single Security Analysis Feature

**Interactive Selector**
- Bond ticker dropdown selector (alphabetically sorted)
- Selected bond highlighted in scatter plot with gold star ⭐

**Current Metrics Cards**
- YTM (Yield to Maturity)
- OAS (Option-Adjusted Spread)
- Z-Score (color-coded: green/yellow/red)

**Scenario Analysis Table**
- Actual Yield vs Fair Yield comparison
- Residual and Z-Score display
- Automated interpretation: Rich/Cheap/Fair
- Trading recommendation: Buy/Sell/Hold

---

## 2026-01-22 (Phase 1.5: UI/UX Enhancement)

### 📱 Mobile-First Redesign

**Complete UI Overhaul**
- Bloomberg/Aladdin-inspired dark theme
- Responsive design optimized for mobile devices
- Custom CSS with glassmorphism effects and smooth animations
- Collapsible filters with mobile-friendly touch targets

### 🌍 Bilingual Interface

**Comprehensive Bilingual Support**
- Complete English and Chinese bilingual support
- All tabs, tooltips, and help text in both languages
- Chinese sector name translations
- Bilingual metric cards and data tables

---

## 2026-01-21 (Phase 1: MVP Launch)

### 🏗️ Core System Implementation

**Architecture Design**
- Complete modular structure setup
- Separation of Module A (AI analysis, future) and Module B (quantitative analysis, current MVP)
- Clear data flow: Load → Clean → Analyze → Visualize

**Data Processing Pipeline**
- Bilingual CSV parsing (automatic Chinese/English column mapping)
- 9-step data cleaning process
- Data validation and quality reporting
- Derived metrics auto-calculation

### 📊 Quantitative Analysis Engine

**PortfolioAnalyzer Class**
- Stratified regression (grouped by sector)
- Quadratic curve fitting
- Z-Score standardization
- Sell candidate identification (Z < -1.5)
- Bleeding asset detection (Net Carry < 0)
- Portfolio metric aggregation
- Executive summary generation

---

## 📊 Development Statistics

| Metric | Value |
|--------|-------|
| **Total Development Time** | 4 days |
| **Current Version** | 3.5 (Phase 3.5) |
| **Lines of Code** | ~5,500 |
| **Python Files** | 15+ |
| **Test Coverage** | In progress |
| **Bonds Supported** | 1,000+ |
| **Issuers Supported** | 200+ |
| **Financial Data Points** | 10,000+ |

---

**🚀 Continuous iteration...**

If you're interested in the project's evolution, feel free to Watch this repository for latest updates!
