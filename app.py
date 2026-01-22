"""
Alpha-One Credit Cockpit - Institutional Grade Dashboard
信用驾驶舱 - 机构级仪表板

A Fixed Income Portfolio Analysis Application for Portfolio Managers.
专为投资组合经理设计的固定收益组合分析应用。

Features:
- Mobile-first responsive design
- Dark mode institutional UI (Bloomberg/Aladdin style)
- Bilingual interface (English/Chinese)
- Rich/Cheap bond identification via stratified regression
- Net Carry efficiency analysis
"""

import io
import sys
from pathlib import Path
from typing import Optional
import importlib

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent))

# Force reload of modules during development to avoid cache issues
import src.module_b.analytics
import src.module_b.data_loader
import src.utils.constants
importlib.reload(src.utils.constants)
importlib.reload(src.module_b.data_loader)
importlib.reload(src.module_b.analytics)

from src.module_b.data_loader import DataLoader, DataValidationError
from src.module_b.analytics import PortfolioAnalyzer
from src.utils.constants import SECTOR_COLORS, Z_SCORE_THRESHOLDS

# ============================================
# PAGE CONFIG & THEME
# ============================================
st.set_page_config(
    page_title="Alpha-One Credit Cockpit | 信用驾驶舱",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="collapsed",  # Collapsed for mobile-first
    menu_items={
        "Get Help": None,
        "Report a bug": None,
        "About": "Alpha-One Credit Cockpit v2.0 | 机构级固收组合分析系统"
    }
)

# ============================================
# INSTITUTIONAL DARK THEME CSS
# ============================================
DARK_THEME_CSS = """
<style>
    /* ====== IMPORTS ====== */
    @import url('https://fonts.googleapis.com/css2?family=Roboto+Mono:wght@400;500;600&family=Inter:wght@400;500;600;700&display=swap');

    /* ====== ROOT VARIABLES ====== */
    :root {
        --bg-primary: #0d1117;
        --bg-secondary: #161b22;
        --bg-tertiary: #21262d;
        --bg-card: rgba(33, 38, 45, 0.85);
        --border-color: #30363d;
        --border-accent: #58a6ff;
        --text-primary: #e6edf3;
        --text-secondary: #8b949e;
        --text-muted: #6e7681;
        --accent-blue: #58a6ff;
        --accent-green: #3fb950;
        --accent-red: #f85149;
        --accent-yellow: #d29922;
        --accent-purple: #a371f7;
        --font-mono: 'Roboto Mono', 'Consolas', 'Monaco', monospace;
        --font-sans: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    }

    /* ====== GLOBAL STYLES ====== */
    .stApp {
        background: linear-gradient(180deg, var(--bg-primary) 0%, #0a0e14 100%);
        color: var(--text-primary);
        font-family: var(--font-sans);
    }

    /* Hide Streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    .stDeployButton {display: none;}

    /* ====== HEADER STYLES ====== */
    .main-header {
        font-size: clamp(1.5rem, 5vw, 2.5rem);
        font-weight: 700;
        background: linear-gradient(135deg, var(--accent-blue) 0%, var(--accent-purple) 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        margin-bottom: 0.25rem;
        letter-spacing: -0.02em;
    }

    .sub-header {
        font-size: clamp(0.75rem, 2.5vw, 1rem);
        color: var(--text-secondary);
        margin-bottom: 1.5rem;
        font-weight: 400;
    }

    .section-header {
        font-size: clamp(1rem, 3vw, 1.25rem);
        font-weight: 600;
        color: var(--text-primary);
        margin: 1.5rem 0 1rem 0;
        padding-bottom: 0.5rem;
        border-bottom: 1px solid var(--border-color);
    }

    /* ====== METRIC CARDS ====== */
    .metric-card {
        background: var(--bg-card);
        backdrop-filter: blur(10px);
        border: 1px solid var(--border-color);
        border-radius: 12px;
        padding: 1rem;
        margin-bottom: 0.75rem;
        transition: all 0.2s ease;
    }

    .metric-card:hover {
        border-color: var(--border-accent);
        box-shadow: 0 4px 20px rgba(88, 166, 255, 0.1);
    }

    .metric-label {
        font-size: 0.7rem;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        color: var(--text-secondary);
        margin-bottom: 0.25rem;
        font-weight: 500;
    }

    .metric-value {
        font-family: var(--font-mono);
        font-size: clamp(1.25rem, 4vw, 1.75rem);
        font-weight: 600;
        color: var(--text-primary);
        line-height: 1.2;
    }

    .metric-delta {
        font-family: var(--font-mono);
        font-size: 0.75rem;
        margin-top: 0.25rem;
    }

    .metric-delta.positive { color: var(--accent-green); }
    .metric-delta.negative { color: var(--accent-red); }
    .metric-delta.neutral { color: var(--text-muted); }

    /* Card variants */
    .metric-card.accent-blue { border-left: 3px solid var(--accent-blue); }
    .metric-card.accent-green { border-left: 3px solid var(--accent-green); }
    .metric-card.accent-red { border-left: 3px solid var(--accent-red); }
    .metric-card.accent-yellow { border-left: 3px solid var(--accent-yellow); }

    /* ====== BOND CARD (Mobile View) ====== */
    .bond-card {
        background: var(--bg-card);
        border: 1px solid var(--border-color);
        border-radius: 10px;
        padding: 0.875rem;
        margin-bottom: 0.5rem;
    }

    .bond-card-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 0.5rem;
    }

    .bond-ticker {
        font-family: var(--font-mono);
        font-weight: 600;
        font-size: 0.9rem;
        color: var(--accent-blue);
    }

    .bond-zscore {
        font-family: var(--font-mono);
        font-size: 0.8rem;
        padding: 0.125rem 0.5rem;
        border-radius: 4px;
    }

    .bond-zscore.rich {
        background: rgba(248, 81, 73, 0.2);
        color: var(--accent-red);
    }

    .bond-zscore.cheap {
        background: rgba(63, 185, 80, 0.2);
        color: var(--accent-green);
    }

    .bond-zscore.fair {
        background: rgba(139, 148, 158, 0.2);
        color: var(--text-secondary);
    }

    .bond-name {
        font-size: 0.75rem;
        color: var(--text-secondary);
        margin-bottom: 0.5rem;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
    }

    .bond-metrics {
        display: grid;
        grid-template-columns: repeat(3, 1fr);
        gap: 0.5rem;
    }

    .bond-metric {
        text-align: center;
    }

    .bond-metric-label {
        font-size: 0.6rem;
        color: var(--text-muted);
        text-transform: uppercase;
    }

    .bond-metric-value {
        font-family: var(--font-mono);
        font-size: 0.8rem;
        color: var(--text-primary);
    }

    /* ====== STREAMLIT OVERRIDES ====== */
    /* Tabs */
    .stTabs [data-baseweb="tab-list"] {
        gap: 0;
        background: var(--bg-secondary);
        border-radius: 8px;
        padding: 4px;
    }

    .stTabs [data-baseweb="tab"] {
        background: transparent;
        border-radius: 6px;
        color: var(--text-secondary);
        font-weight: 500;
        padding: 0.5rem 1rem;
        font-size: 0.875rem;
    }

    .stTabs [aria-selected="true"] {
        background: var(--bg-tertiary);
        color: var(--text-primary);
    }

    /* Expander */
    .streamlit-expanderHeader {
        background: var(--bg-secondary);
        border: 1px solid var(--border-color);
        border-radius: 8px;
        color: var(--text-primary);
        font-weight: 500;
    }

    .streamlit-expanderContent {
        background: var(--bg-secondary);
        border: 1px solid var(--border-color);
        border-top: none;
        border-radius: 0 0 8px 8px;
    }

    /* Buttons */
    .stButton > button {
        background: linear-gradient(135deg, var(--accent-blue) 0%, var(--accent-purple) 100%);
        color: white;
        border: none;
        border-radius: 8px;
        font-weight: 600;
        padding: 0.5rem 1.5rem;
        transition: all 0.2s ease;
    }

    .stButton > button:hover {
        transform: translateY(-1px);
        box-shadow: 0 4px 12px rgba(88, 166, 255, 0.3);
    }

    /* Checkbox */
    .stCheckbox label {
        color: var(--text-primary);
    }

    /* Selectbox & Multiselect */
    .stSelectbox > div > div,
    .stMultiSelect > div > div {
        background: var(--bg-tertiary);
        border-color: var(--border-color);
        color: var(--text-primary);
    }

    /* Slider */
    .stSlider > div > div > div {
        background: var(--accent-blue);
    }

    /* Dataframe */
    .stDataFrame {
        border: 1px solid var(--border-color);
        border-radius: 8px;
        overflow: hidden;
    }

    .stDataFrame [data-testid="stDataFrameResizable"] {
        background: var(--bg-secondary);
    }

    /* File uploader */
    .stFileUploader > div {
        background: var(--bg-tertiary);
        border: 1px dashed var(--border-color);
        border-radius: 8px;
    }

    /* Divider */
    hr {
        border-color: var(--border-color);
        margin: 1.5rem 0;
    }

    /* ====== MOBILE RESPONSIVE ====== */
    @media (max-width: 768px) {
        .main-header {
            text-align: center;
        }

        .sub-header {
            text-align: center;
        }

        .metric-card {
            padding: 0.75rem;
        }

        .metric-value {
            font-size: 1.25rem;
        }

        .stTabs [data-baseweb="tab"] {
            padding: 0.4rem 0.6rem;
            font-size: 0.75rem;
        }

        /* Stack columns vertically */
        [data-testid="column"] {
            width: 100% !important;
            flex: 1 1 100% !important;
            min-width: 100% !important;
        }
    }

    /* ====== PLOTLY DARK THEME ====== */
    .js-plotly-plot .plotly .modebar {
        background: var(--bg-secondary) !important;
    }

    .js-plotly-plot .plotly .modebar-btn path {
        fill: var(--text-secondary) !important;
    }

    /* ====== SCROLLBAR ====== */
    ::-webkit-scrollbar {
        width: 8px;
        height: 8px;
    }

    ::-webkit-scrollbar-track {
        background: var(--bg-secondary);
    }

    ::-webkit-scrollbar-thumb {
        background: var(--border-color);
        border-radius: 4px;
    }

    ::-webkit-scrollbar-thumb:hover {
        background: var(--text-muted);
    }

    /* ====== STATUS INDICATORS ====== */
    .status-badge {
        display: inline-block;
        padding: 0.125rem 0.5rem;
        border-radius: 4px;
        font-size: 0.7rem;
        font-weight: 500;
        text-transform: uppercase;
    }

    .status-badge.rich {
        background: rgba(248, 81, 73, 0.15);
        color: var(--accent-red);
        border: 1px solid rgba(248, 81, 73, 0.3);
    }

    .status-badge.cheap {
        background: rgba(63, 185, 80, 0.15);
        color: var(--accent-green);
        border: 1px solid rgba(63, 185, 80, 0.3);
    }

    .status-badge.bleeding {
        background: rgba(210, 153, 34, 0.15);
        color: var(--accent-yellow);
        border: 1px solid rgba(210, 153, 34, 0.3);
    }
</style>
"""

# ============================================
# BILINGUAL LABELS
# ============================================
LABELS = {
    # Headers
    "app_title": "Alpha-One Credit Cockpit",
    "app_subtitle": "Fixed Income Portfolio Optimizer | 固定收益组合优化器",

    # Tabs
    "tab_matrix": "Relative Value / 相对价值",
    "tab_optimization": "Alpha Lab / 阿尔法实验室",
    "tab_brief": "Executive Brief / 管理简报",

    # Sections
    "portfolio_overview": "Portfolio Overview / 组合概览",
    "filter_settings": "Filter Settings / 筛选条件",
    "data_source": "Data Source / 数据源",
    "duration_yield_matrix": "Duration-Yield Matrix / 久期-收益率矩阵",
    "sell_candidates": "Sell Candidates / 卖出候选",
    "bleeding_assets": "Bleeding Assets / 失血资产",
    "carry_distribution": "Carry Distribution / 息差分布",
    "sector_allocation": "Sector Allocation / 板块配置",
    "data_export": "Data Export / 数据导出",

    # Metrics
    "total_aum": "Total AUM / 总资产",
    "holdings": "Holdings / 持仓数",
    "duration": "Duration / 久期",
    "ytm": "YTM / 到期收益率",
    "oas": "OAS / 期权调整利差",
    "notional": "Notional / 名义本金",
    "net_carry": "Net Carry / 净息差",
    "carry_eff": "Carry Eff. / 息差效率",
    "z_score": "Z-Score / Z分数",
    "ftp": "FTP / 资金成本",
    "sector": "Sector / 板块",
    "accounting": "Accounting / 会计分类",
    "tradeable": "Tradeable / 可交易",
    "htim_locked": "HTM Locked / HTM锁定",
    "negative_carry": "Neg. Carry / 负息差",
    "wtd_duration": "Wtd Duration / 加权久期",
    "wtd_yield": "Wtd Yield / 加权收益",
    "wtd_carry": "Wtd Carry / 加权息差",

    # Actions
    "upload_csv": "Upload Portfolio CSV / 上传组合CSV",
    "use_sample": "Use Sample Data / 使用示例数据",
    "exclude_htm": "Exclude HTM / 排除持有至到期",
    "min_liquidity": "Min Liquidity / 最低流动性",
    "generate_summary": "Generate Summary / 生成摘要",
    "download_csv": "Download CSV / 下载CSV",
    "download_summary": "Download Summary / 下载摘要",

    # Mobile
    "mobile_view": "Mobile View / 移动视图",
    "show_more": "Show More / 显示更多",

    # Status
    "data_loaded": "Data Loaded / 数据已加载",
    "no_data": "No data available / 暂无数据",
    "loading": "Loading... / 加载中...",
}

# Sector name translations
SECTOR_NAMES_CN = {
    "MBS": "抵押贷款证券",
    "Corps": "公司债",
    "Fins": "金融债",
    "Rates": "利率债",
    "EM": "新兴市场",
    "ABS": "资产支持证券",
    "CMBS": "商业抵押证券",
    "CLO": "贷款抵押证券",
    "Munis": "市政债",
    "Sovs": "主权债",
}

# ============================================
# PLOTLY DARK THEME HELPER
# ============================================
def apply_dark_theme(fig, **kwargs):
    """Apply dark theme to a Plotly figure with optional overrides."""
    # Base dark theme settings
    fig.update_layout(
        paper_bgcolor="rgba(13, 17, 23, 0)",
        plot_bgcolor="rgba(22, 27, 34, 0.5)",
        font=dict(color="#e6edf3", family="Inter, sans-serif"),
        hoverlabel=dict(
            bgcolor="#21262d",
            bordercolor="#30363d",
            font=dict(color="#e6edf3", family="Roboto Mono, monospace"),
        ),
        **kwargs
    )

    # Update axes
    fig.update_xaxes(
        gridcolor="rgba(48, 54, 61, 0.5)",
        linecolor="#30363d",
        tickfont=dict(color="#8b949e"),
        title_font=dict(color="#8b949e"),
    )

    fig.update_yaxes(
        gridcolor="rgba(48, 54, 61, 0.5)",
        linecolor="#30363d",
        tickfont=dict(color="#8b949e"),
        title_font=dict(color="#8b949e"),
    )

    return fig

# Updated sector colors for dark theme
DARK_SECTOR_COLORS = {
    "MBS": "#58a6ff",
    "Corps": "#a371f7",
    "Fins": "#3fb950",
    "Rates": "#f0883e",
    "EM": "#f85149",
    "ABS": "#db61a2",
    "CMBS": "#79c0ff",
    "CLO": "#56d4dd",
    "Munis": "#d29922",
    "Sovs": "#8b949e",
    "Other": "#6e7681",
}


# ============================================
# UTILITY FUNCTIONS
# ============================================
def format_currency(value: float, short: bool = True) -> str:
    """Format value as currency with proper alignment."""
    if pd.isna(value):
        return "—"
    if short:
        if abs(value) >= 1e9:
            return f"${value/1e9:.2f}B"
        elif abs(value) >= 1e6:
            return f"${value/1e6:.1f}M"
        elif abs(value) >= 1e3:
            return f"${value/1e3:.0f}K"
    return f"${value:,.0f}"


def format_percentage(value: float, decimals: int = 2) -> str:
    """Format value as percentage."""
    if pd.isna(value):
        return "—"
    return f"{value * 100:.{decimals}f}%"


def format_number(value: float, decimals: int = 2) -> str:
    """Format number with proper decimals."""
    if pd.isna(value):
        return "—"
    return f"{value:.{decimals}f}"


def get_z_score_class(z_score: float) -> str:
    """Get CSS class based on Z-score."""
    if pd.isna(z_score):
        return "fair"
    if z_score < -1.5:
        return "rich"
    elif z_score > 1.5:
        return "cheap"
    return "fair"


def get_z_score_label(z_score: float) -> str:
    """Get label based on Z-score."""
    if pd.isna(z_score):
        return "Fair"
    if z_score < -1.5:
        return "Rich / 贵"
    elif z_score > 1.5:
        return "Cheap / 便宜"
    return "Fair / 公允"


def render_metric_card(
    label: str,
    value: str,
    delta: Optional[str] = None,
    delta_type: str = "neutral",
    accent: str = "blue"
) -> str:
    """Render a styled metric card."""
    delta_html = ""
    if delta:
        delta_html = f'<div class="metric-delta {delta_type}">{delta}</div>'

    return f"""
    <div class="metric-card accent-{accent}">
        <div class="metric-label">{label}</div>
        <div class="metric-value">{value}</div>
        {delta_html}
    </div>
    """


def render_bond_card(row: pd.Series) -> str:
    """Render a mobile-friendly bond card."""
    z_class = get_z_score_class(row.get("Z_Score", 0))
    z_label = f"{row.get('Z_Score', 0):.2f}" if not pd.isna(row.get("Z_Score")) else "—"

    name = row.get("Name", "N/A")
    if len(name) > 35:
        name = name[:32] + "..."

    return f"""
    <div class="bond-card">
        <div class="bond-card-header">
            <span class="bond-ticker">{row.get('Ticker', 'N/A')}</span>
            <span class="bond-zscore {z_class}">Z: {z_label}</span>
        </div>
        <div class="bond-name">{name}</div>
        <div class="bond-metrics">
            <div class="bond-metric">
                <div class="bond-metric-label">YTM</div>
                <div class="bond-metric-value">{format_percentage(row.get('Yield', 0))}</div>
            </div>
            <div class="bond-metric">
                <div class="bond-metric-label">DUR</div>
                <div class="bond-metric-value">{format_number(row.get('Duration', 0), 1)}y</div>
            </div>
            <div class="bond-metric">
                <div class="bond-metric-label">OAS</div>
                <div class="bond-metric-value">{format_number(row.get('OAS', 0), 0)}bp</div>
            </div>
        </div>
    </div>
    """


# ============================================
# MAIN APPLICATION
# ============================================
def main():
    """Main application entry point."""
    # Inject dark theme CSS
    st.markdown(DARK_THEME_CSS, unsafe_allow_html=True)

    # Header
    st.markdown(f'<h1 class="main-header">{LABELS["app_title"]}</h1>', unsafe_allow_html=True)
    st.markdown(f'<p class="sub-header">{LABELS["app_subtitle"]}</p>', unsafe_allow_html=True)

    # Initialize session state
    if "data_loaded" not in st.session_state:
        st.session_state.data_loaded = False
    if "df" not in st.session_state:
        st.session_state.df = None
    if "analyzer" not in st.session_state:
        st.session_state.analyzer = None
    if "mobile_view" not in st.session_state:
        st.session_state.mobile_view = False
    if "model_type" not in st.session_state:
        st.session_state.model_type = "quadratic"
    if "selected_ticker" not in st.session_state:
        st.session_state.selected_ticker = None

    # ============================================
    # FILTERS (Main Page Expander for Mobile)
    # ============================================
    with st.expander(f"⚙️ {LABELS['filter_settings']}", expanded=False):
        # Add model selection at the top
        st.markdown("**🔬 Curve Model / 曲线模型**")
        model_col1, model_col2 = st.columns(2)
        with model_col1:
            model_type = st.radio(
                "Select Model",
                options=["quadratic", "nelson_siegel"],
                format_func=lambda x: "📉 Quadratic (Polynomial)" if x == "quadratic" else "📐 Nelson-Siegel (Advanced)",
                horizontal=True,
                label_visibility="collapsed",
                key="model_selector"
            )
            st.session_state.model_type = model_type

        st.markdown("---")

        filter_col1, filter_col2, filter_col3 = st.columns([2, 2, 1])

        with filter_col1:
            # Data Upload
            st.markdown(f"**{LABELS['data_source']}**")
            uploaded_file = st.file_uploader(
                LABELS["upload_csv"],
                type=["csv"],
                help="Upload your portfolio export file (supports bilingual columns)",
                label_visibility="collapsed",
            )
            use_sample = st.checkbox(LABELS["use_sample"], value=not uploaded_file)

        with filter_col2:
            st.markdown("**Filters / 筛选器**")
            exclude_htm = st.checkbox(
                LABELS["exclude_htm"],
                value=True,
                help="HTM bonds cannot be sold due to regulations / HTM债券因法规限制不能出售",
            )

            if st.session_state.data_loaded and st.session_state.df is not None:
                available_sectors = sorted(st.session_state.df["Sector_L1"].unique())
                selected_sectors = st.multiselect(
                    f"{LABELS['sector']}",
                    options=available_sectors,
                    default=available_sectors,
                )
            else:
                selected_sectors = []

        with filter_col3:
            st.markdown("**View / 视图**")
            st.session_state.mobile_view = st.checkbox(
                LABELS["mobile_view"],
                value=st.session_state.mobile_view,
                help="Optimized for mobile screens / 针对移动屏幕优化"
            )

            if st.session_state.data_loaded:
                min_liquidity = st.slider(
                    LABELS["min_liquidity"],
                    min_value=1,
                    max_value=5,
                    value=1,
                )
            else:
                min_liquidity = 1

    # ============================================
    # DATA LOADING
    # ============================================
    if uploaded_file or use_sample:
        try:
            loader = DataLoader()

            if uploaded_file:
                df = loader.load_from_upload(uploaded_file)
            else:
                sample_path = Path(__file__).parent / "data" / "portfolio.csv"
                if sample_path.exists():
                    df = loader.load(sample_path)
                else:
                    st.error("Sample data not found. Please upload a CSV file.")
                    st.error("示例数据未找到，请上传CSV文件。")
                    return

            # Fit curves with selected model
            analyzer = PortfolioAnalyzer(df, model_type=st.session_state.model_type)
            analyzer.fit_sector_curves()

            st.session_state.df = df
            st.session_state.analyzer = analyzer
            st.session_state.data_loaded = True
            st.session_state.quality_report = loader.get_quality_report()

        except DataValidationError as e:
            st.error(f"Data validation error: {e}")
            return
        except Exception as e:
            st.error(f"Error loading data: {e}")
            return

    if not st.session_state.data_loaded:
        st.info("☝️ Expand 'Filter Settings' above to upload data or use sample data")
        st.info("☝️ 展开上方'筛选条件'上传数据或使用示例数据")
        return

    # Get filtered data
    analyzer = st.session_state.analyzer
    df_filtered = analyzer.get_filtered_data(
        exclude_htm=exclude_htm,
        sectors=selected_sectors if selected_sectors else None,
        min_liquidity=min_liquidity,
    )

    # Re-fit curves on filtered data with selected model
    filtered_analyzer = PortfolioAnalyzer(df_filtered, model_type=st.session_state.model_type)
    filtered_analyzer.fit_sector_curves()

    # ============================================
    # KPI METRICS ROW
    # ============================================
    st.markdown(f'<div class="section-header">{LABELS["portfolio_overview"]}</div>', unsafe_allow_html=True)

    metrics = filtered_analyzer.calculate_portfolio_metrics()

    # Use 4 columns that will stack on mobile
    kpi_col1, kpi_col2, kpi_col3, kpi_col4 = st.columns(4)

    with kpi_col1:
        st.markdown(render_metric_card(
            LABELS["total_aum"],
            format_currency(metrics.total_aum),
            f"{len(df_filtered):,} bonds",
            "neutral",
            "blue"
        ), unsafe_allow_html=True)

    with kpi_col2:
        st.markdown(render_metric_card(
            LABELS["wtd_duration"],
            f"{metrics.weighted_duration:.2f}y",
            None,
            "neutral",
            "purple"
        ), unsafe_allow_html=True)

    with kpi_col3:
        carry_delta_type = "positive" if metrics.weighted_net_carry > 0 else "negative"
        st.markdown(render_metric_card(
            LABELS["wtd_carry"],
            format_percentage(metrics.weighted_net_carry),
            f"{metrics.negative_carry_count} bleeding" if metrics.negative_carry_count > 0 else "All positive",
            carry_delta_type,
            "green" if metrics.weighted_net_carry > 0 else "red"
        ), unsafe_allow_html=True)

    with kpi_col4:
        st.markdown(render_metric_card(
            LABELS["htim_locked"],
            f"{metrics.htim_count}",
            format_currency(metrics.htm_exposure),
            "neutral",
            "yellow"
        ), unsafe_allow_html=True)

    # ============================================
    # MAIN TABS
    # ============================================
    tab1, tab2, tab3 = st.tabs([
        f"📈 {LABELS['tab_matrix']}",
        f"🔬 {LABELS['tab_optimization']}",
        f"📋 {LABELS['tab_brief']}",
    ])

    # ============================================
    # TAB 1: RELATIVE VALUE MATRIX
    # ============================================
    with tab1:
        st.markdown(f'<div class="section-header">{LABELS["duration_yield_matrix"]}</div>', unsafe_allow_html=True)

        # Build scatter plot with dark theme
        fig = go.Figure()

        # Get selected ticker from session state
        highlighted_ticker = st.session_state.get("selected_ticker", None)

        for sector in (selected_sectors or []):
            sector_data = df_filtered[df_filtered["Sector_L1"] == sector]
            if len(sector_data) == 0:
                continue

            color = DARK_SECTOR_COLORS.get(sector, "#6e7681")
            sector_cn = SECTOR_NAMES_CN.get(sector, sector)

            # Split data into selected and non-selected
            if highlighted_ticker:
                non_selected = sector_data[sector_data["Ticker"] != highlighted_ticker]
            else:
                non_selected = sector_data

            # Create bilingual hover text for non-selected
            hover_text = non_selected.apply(
                lambda row: (
                    f"<b>{row['Ticker']}</b><br>"
                    f"名称: {row.get('Name', 'N/A')}<br>"
                    f"━━━━━━━━━━━━<br>"
                    f"YTM / 收益率: {row['Yield']*100:.2f}%<br>"
                    f"Duration / 久期: {row['Duration']:.2f}y<br>"
                    f"OAS / 利差: {row['OAS']:.0f}bp<br>"
                    f"Net Carry / 净息差: {row['Net_Carry']*100:.2f}%<br>"
                    f"Z-Score / Z分数: {row['Z_Score']:.2f}<br>"
                    f"━━━━━━━━━━━━<br>"
                    f"Notional / 本金: {format_currency(row['Nominal_USD'])}"
                ),
                axis=1,
            )

            # Size based on nominal (normalized)
            sizes = np.clip(non_selected["Nominal_USD"] / 1e6, 5, 25)

            # Add non-selected bonds
            fig.add_trace(go.Scatter(
                x=non_selected["Duration"],
                y=non_selected["Yield"] * 100,
                mode="markers",
                name=f"{sector} / {sector_cn}",
                marker=dict(
                    size=sizes,
                    color=color,
                    opacity=0.8,
                    line=dict(width=1, color="rgba(255,255,255,0.3)"),
                ),
                hovertemplate="%{hovertext}<extra></extra>",
                hovertext=hover_text,
            ))

            # Add fitted curve
            regression_results = filtered_analyzer.get_regression_results()
            if sector in regression_results:
                try:
                    x_curve, y_curve = filtered_analyzer.get_curve_points(sector, n_points=50)
                    fig.add_trace(go.Scatter(
                        x=x_curve,
                        y=y_curve * 100,
                        mode="lines",
                        name=f"{sector} Curve",
                        line=dict(color=color, width=2, dash="dash"),
                        showlegend=False,
                        hoverinfo="skip",
                    ))
                except Exception:
                    pass

        # Highlight selected ticker with gold star
        if highlighted_ticker and highlighted_ticker in df_filtered["Ticker"].values:
            selected_bond = df_filtered[df_filtered["Ticker"] == highlighted_ticker].iloc[0]

            hover_text_selected = (
                f"<b>⭐ {selected_bond['Ticker']} (SELECTED)</b><br>"
                f"名称: {selected_bond.get('Name', 'N/A')}<br>"
                f"━━━━━━━━━━━━<br>"
                f"YTM / 收益率: {selected_bond['Yield']*100:.2f}%<br>"
                f"Duration / 久期: {selected_bond['Duration']:.2f}y<br>"
                f"OAS / 利差: {selected_bond['OAS']:.0f}bp<br>"
                f"Net Carry / 净息差: {selected_bond['Net_Carry']*100:.2f}%<br>"
                f"Z-Score / Z分数: {selected_bond['Z_Score']:.2f}<br>"
                f"━━━━━━━━━━━━<br>"
                f"Notional / 本金: {format_currency(selected_bond['Nominal_USD'])}"
            )

            fig.add_trace(go.Scatter(
                x=[selected_bond["Duration"]],
                y=[selected_bond["Yield"] * 100],
                mode="markers",
                name="Selected / 选中",
                marker=dict(
                    size=30,
                    color="#FFD700",  # Gold
                    symbol="star",
                    line=dict(width=3, color="white"),
                ),
                hovertemplate=hover_text_selected + "<extra></extra>",
                showlegend=True,
            ))

        # Apply dark theme layout
        apply_dark_theme(
            fig,
            xaxis_title="Duration / 久期 (Years)",
            yaxis_title="YTM / 到期收益率 (%)",
            hovermode="closest",
            height=500,
            margin=dict(l=60, r=20, t=40, b=60),
            legend=dict(
                orientation="h",
                yanchor="top",
                y=-0.15,
                xanchor="center",
                x=0.5,
                bgcolor="rgba(22, 27, 34, 0.8)",
                bordercolor="#30363d",
                font=dict(size=10, color="#e6edf3"),
            ),
        )

        st.plotly_chart(fig, use_container_width=True)

        # Model Parameters and Statistics
        with st.expander("📊 Model Stats & Parameters / 模型统计与参数"):
            regression_results = filtered_analyzer.get_regression_results()
            if regression_results:
                stats_data = []
                for sector, r in regression_results.items():
                    sector_display = f"{sector} / {SECTOR_NAMES_CN.get(sector, sector)}"
                    base_stats = {
                        f"{LABELS['sector']}": sector_display,
                        "R²": f"{r.r_squared:.4f}",
                        "N": r.sample_count,
                        "Dur Range": f"{r.duration_range[0]:.1f}-{r.duration_range[1]:.1f}",
                        "Residual σ": f"{r.residual_std*100:.2f}%",
                    }

                    # Add model-specific parameters
                    if st.session_state.model_type == "nelson_siegel":
                        base_stats.update({
                            "β₀ (Long)": f"{r.beta_0*100:.2f}%",
                            "β₁ (Short)": f"{r.beta_1*100:.2f}%",
                            "β₂ (Curve)": f"{r.beta_2*100:.2f}%",
                            "λ (Decay)": f"{r.lambda_:.2f}",
                        })
                    else:
                        base_stats.update({
                            "Coeff a": f"{r.a:.6f}",
                            "Coeff b": f"{r.b:.4f}",
                            "Coeff c": f"{r.c:.4f}",
                        })

                    stats_data.append(base_stats)

                st.dataframe(pd.DataFrame(stats_data), use_container_width=True, hide_index=True)

                # Add explanation for Nelson-Siegel parameters
                if st.session_state.model_type == "nelson_siegel":
                    st.markdown("""
                    **Nelson-Siegel Parameters:**
                    - **β₀ (Long-Term)**: Long-term yield level as duration → ∞
                    - **β₁ (Short-Term)**: Short-term component (slope at origin)
                    - **β₂ (Curvature)**: Medium-term curvature component
                    - **λ (Decay)**: Controls where the curvature peaks
                    """)

        # ============================================
        # SINGLE SECURITY ANALYSIS
        # ============================================
        st.markdown(f'<div class="section-header">🔍 Single Security Analysis / 单券分析</div>', unsafe_allow_html=True)
        st.markdown("*Drill down into individual securities and compare to sector curve*")
        st.markdown("*深入分析单个证券并与板块曲线对比*")

        # Ticker selection
        ticker_col1, ticker_col2 = st.columns([2, 1])

        with ticker_col1:
            available_tickers = sorted(df_filtered["Ticker"].unique())
            selected_ticker = st.selectbox(
                "Select Ticker / 选择代码",
                options=[""] + available_tickers,
                format_func=lambda x: "-- Select a ticker --" if x == "" else x,
                key="ticker_selector"
            )

        if selected_ticker and selected_ticker != "":
            st.session_state.selected_ticker = selected_ticker

            # Get bond details
            bond_data = df_filtered[df_filtered["Ticker"] == selected_ticker].iloc[0]

            # Display bond information
            bond_col1, bond_col2, bond_col3 = st.columns(3)

            with bond_col1:
                st.markdown(render_metric_card(
                    "Current YTM / 当前收益率",
                    format_percentage(bond_data["Yield"]),
                    None,
                    "neutral",
                    "blue"
                ), unsafe_allow_html=True)

            with bond_col2:
                st.markdown(render_metric_card(
                    "OAS / 期权调整利差",
                    f"{bond_data['OAS']:.0f} bp",
                    None,
                    "neutral",
                    "purple"
                ), unsafe_allow_html=True)

            with bond_col3:
                z_class = get_z_score_class(bond_data["Z_Score"])
                z_accent = "red" if z_class == "rich" else "green" if z_class == "cheap" else "yellow"
                st.markdown(render_metric_card(
                    "Z-Score / Z分数",
                    f"{bond_data['Z_Score']:.2f}" if not pd.isna(bond_data['Z_Score']) else "N/A",
                    get_z_score_label(bond_data["Z_Score"]),
                    "neutral",
                    z_accent
                ), unsafe_allow_html=True)

            # Scenario Analysis Table
            st.markdown("**📊 Scenario Analysis / 情景分析**")

            scenario_col1, scenario_col2 = st.columns([2, 1])

            with scenario_col1:
                # Calculate fair value from model
                fair_yield = bond_data.get("Model_Yield", bond_data["Yield"])
                residual = bond_data.get("Residual", 0)

                scenario_data = {
                    "Metric / 指标": [
                        "Actual Yield / 实际收益率",
                        "Fair Yield (Model) / 公允收益率（模型）",
                        "Residual / 残差",
                        "Z-Score / Z分数",
                        "Interpretation / 解释"
                    ],
                    "Value / 数值": [
                        format_percentage(bond_data["Yield"]),
                        format_percentage(fair_yield),
                        f"{residual*100:.2f}%" if not pd.isna(residual) else "N/A",
                        f"{bond_data['Z_Score']:.2f}" if not pd.isna(bond_data['Z_Score']) else "N/A",
                        get_z_score_label(bond_data["Z_Score"])
                    ]
                }

                st.dataframe(pd.DataFrame(scenario_data), use_container_width=True, hide_index=True)

            with scenario_col2:
                st.markdown("**📝 Notes / 注释**")
                if not pd.isna(bond_data['Z_Score']):
                    if bond_data['Z_Score'] < -1.5:
                        st.markdown("⚠️ **Trading Rich / 偏贵**")
                        st.markdown("Consider selling / 考虑卖出")
                    elif bond_data['Z_Score'] > 1.5:
                        st.markdown("✅ **Trading Cheap / 偏便宜**")
                        st.markdown("Consider buying / 考虑买入")
                    else:
                        st.markdown("ℹ️ **Fair Value / 公允价值**")
                        st.markdown("Hold / 持有")

            # Issuer Curve Analysis
            st.markdown("**🏢 Issuer Curve / 发行人曲线**")

            # Extract issuer from ticker or name (simple heuristic)
            issuer = selected_ticker.split()[0] if " " in selected_ticker else selected_ticker[:3]

            # Find sibling bonds (same issuer)
            sibling_mask = df_filtered["Ticker"].str.contains(issuer, case=False, na=False)
            sibling_bonds = df_filtered[sibling_mask]

            if len(sibling_bonds) > 1:
                st.markdown(f"*Found {len(sibling_bonds)} bonds from issuer: {issuer} / 发现 {len(sibling_bonds)} 个来自发行人 {issuer} 的债券*")

                # Create issuer-specific curve chart
                fig_issuer = go.Figure()

                # Plot all sibling bonds
                for idx, row in sibling_bonds.iterrows():
                    is_selected = row["Ticker"] == selected_ticker
                    marker_size = 20 if is_selected else 12
                    marker_color = "#FFD700" if is_selected else DARK_SECTOR_COLORS.get(row["Sector_L1"], "#6e7681")
                    marker_symbol = "star" if is_selected else "circle"

                    hover_text = (
                        f"<b>{row['Ticker']}</b><br>"
                        f"YTM: {row['Yield']*100:.2f}%<br>"
                        f"Duration: {row['Duration']:.2f}y<br>"
                        f"OAS: {row['OAS']:.0f}bp<br>"
                        f"Z-Score: {row['Z_Score']:.2f}"
                    )

                    fig_issuer.add_trace(go.Scatter(
                        x=[row["Duration"]],
                        y=[row["Yield"] * 100],
                        mode="markers",
                        name=row["Ticker"],
                        marker=dict(
                            size=marker_size,
                            color=marker_color,
                            symbol=marker_symbol,
                            line=dict(width=2, color="white" if is_selected else "rgba(255,255,255,0.3)"),
                        ),
                        hovertemplate=hover_text + "<extra></extra>",
                        showlegend=False,
                    ))

                # Add sector curve if available
                sector = bond_data["Sector_L1"]
                regression_results = filtered_analyzer.get_regression_results()
                if sector in regression_results:
                    try:
                        x_curve, y_curve = filtered_analyzer.get_curve_points(sector, n_points=50)
                        fig_issuer.add_trace(go.Scatter(
                            x=x_curve,
                            y=y_curve * 100,
                            mode="lines",
                            name=f"{sector} Curve",
                            line=dict(color=DARK_SECTOR_COLORS.get(sector, "#6e7681"), width=2, dash="dash"),
                            hoverinfo="skip",
                        ))
                    except Exception:
                        pass

                apply_dark_theme(
                    fig_issuer,
                    xaxis_title="Duration / 久期 (Years)",
                    yaxis_title="YTM / 到期收益率 (%)",
                    hovermode="closest",
                    height=350,
                    margin=dict(l=60, r=20, t=40, b=60),
                    title=f"Issuer Curve: {issuer}",
                )

                st.plotly_chart(fig_issuer, use_container_width=True)
            else:
                st.info(f"Only one bond found for issuer {issuer}. / 该发行人仅有一个债券。")
        else:
            st.info("☝️ Select a ticker above to see detailed analysis / 选择上方的代码查看详细分析")

    # ============================================
    # TAB 2: ALPHA OPTIMIZATION LAB
    # ============================================
    with tab2:
        opt_col1, opt_col2 = st.columns(2)

        # SELL CANDIDATES
        with opt_col1:
            st.markdown(f'<div class="section-header">🔴 {LABELS["sell_candidates"]}</div>', unsafe_allow_html=True)
            st.markdown("*Z-Score < -1.5 | Expensive relative to sector curve*")
            st.markdown("*Z分数 < -1.5 | 相对板块曲线偏贵*")

            sell_candidates = filtered_analyzer.get_sell_candidates(
                z_threshold=-1.5,
                exclude_htm=exclude_htm,
            )

            if len(sell_candidates) > 0:
                if st.session_state.mobile_view:
                    # Card view for mobile
                    for idx, row in sell_candidates.head(5).iterrows():
                        st.markdown(render_bond_card(row), unsafe_allow_html=True)
                    if len(sell_candidates) > 5:
                        with st.expander(f"{LABELS['show_more']} ({len(sell_candidates)-5} more)"):
                            for idx, row in sell_candidates.iloc[5:].iterrows():
                                st.markdown(render_bond_card(row), unsafe_allow_html=True)
                else:
                    # Table view for desktop
                    display_cols = ["Ticker", "Name", "Sector_L1", "Duration", "Yield", "Net_Carry", "Z_Score", "Nominal_USD"]
                    display_cols = [c for c in display_cols if c in sell_candidates.columns]

                    styled_df = sell_candidates[display_cols].copy()
                    styled_df.columns = ["Ticker", "Name / 名称", LABELS["sector"],
                                        LABELS["duration"], LABELS["ytm"],
                                        LABELS["net_carry"], LABELS["z_score"], LABELS["notional"]]

                    # Format values
                    styled_df[LABELS["ytm"]] = sell_candidates["Yield"].apply(format_percentage)
                    styled_df[LABELS["net_carry"]] = sell_candidates["Net_Carry"].apply(format_percentage)
                    styled_df[LABELS["notional"]] = sell_candidates["Nominal_USD"].apply(format_currency)
                    styled_df[LABELS["z_score"]] = sell_candidates["Z_Score"].round(2)
                    styled_df[LABELS["duration"]] = sell_candidates["Duration"].round(2)

                    st.dataframe(styled_df, use_container_width=True, hide_index=True)

                # Summary metric
                total_exposure = sell_candidates["Nominal_USD"].sum()
                st.markdown(render_metric_card(
                    "Sell Exposure / 卖出敞口",
                    format_currency(total_exposure),
                    f"{len(sell_candidates)} bonds / 债券",
                    "negative",
                    "red"
                ), unsafe_allow_html=True)
            else:
                st.success("✅ No rich bonds identified / 未发现偏贵债券")

        # BLEEDING ASSETS
        with opt_col2:
            st.markdown(f'<div class="section-header">💸 {LABELS["bleeding_assets"]}</div>', unsafe_allow_html=True)
            st.markdown("*Yield < FTP | Negative carry positions*")
            st.markdown("*收益率 < 资金成本 | 负息差持仓*")

            bleeding_assets = filtered_analyzer.get_bleeding_assets(exclude_htm=exclude_htm)

            if len(bleeding_assets) > 0:
                if st.session_state.mobile_view:
                    # Card view for mobile
                    for idx, row in bleeding_assets.head(5).iterrows():
                        st.markdown(render_bond_card(row), unsafe_allow_html=True)
                    if len(bleeding_assets) > 5:
                        with st.expander(f"{LABELS['show_more']} ({len(bleeding_assets)-5} more)"):
                            for idx, row in bleeding_assets.iloc[5:].iterrows():
                                st.markdown(render_bond_card(row), unsafe_allow_html=True)
                else:
                    # Table view for desktop
                    display_cols = ["Ticker", "Name", "Sector_L1", "Duration", "Yield", "FTP", "Net_Carry", "Nominal_USD"]
                    display_cols = [c for c in display_cols if c in bleeding_assets.columns]

                    styled_df = bleeding_assets[display_cols].copy()
                    styled_df.columns = ["Ticker", "Name / 名称", LABELS["sector"],
                                        LABELS["duration"], LABELS["ytm"],
                                        LABELS["ftp"], LABELS["net_carry"], LABELS["notional"]]

                    styled_df[LABELS["ytm"]] = bleeding_assets["Yield"].apply(format_percentage)
                    styled_df[LABELS["ftp"]] = bleeding_assets["FTP"].apply(format_percentage)
                    styled_df[LABELS["net_carry"]] = bleeding_assets["Net_Carry"].apply(format_percentage)
                    styled_df[LABELS["notional"]] = bleeding_assets["Nominal_USD"].apply(format_currency)
                    styled_df[LABELS["duration"]] = bleeding_assets["Duration"].round(2)

                    st.dataframe(styled_df, use_container_width=True, hide_index=True)

                total_bleed = bleeding_assets["Nominal_USD"].sum()
                annual_drag = abs((bleeding_assets["Net_Carry"] * bleeding_assets["Nominal_USD"]).sum())
                st.markdown(render_metric_card(
                    "Bleeding Exposure / 失血敞口",
                    format_currency(total_bleed),
                    f"Annual Drag: {format_currency(annual_drag)} / 年化拖累",
                    "negative",
                    "yellow"
                ), unsafe_allow_html=True)
            else:
                st.success("✅ No negative carry bonds / 无负息差债券")

        # Carry Distribution Chart
        st.markdown(f'<div class="section-header">📊 {LABELS["carry_distribution"]}</div>', unsafe_allow_html=True)

        fig_carry = go.Figure()

        for sector in (selected_sectors or []):
            sector_data = df_filtered[df_filtered["Sector_L1"] == sector]
            if len(sector_data) == 0:
                continue

            color = DARK_SECTOR_COLORS.get(sector, "#6e7681")

            fig_carry.add_trace(go.Histogram(
                x=sector_data["Carry_Efficiency"] * 100,  # Convert to bps-like
                name=f"{sector} / {SECTOR_NAMES_CN.get(sector, sector)}",
                marker_color=color,
                opacity=0.7,
            ))

        fig_carry.add_vline(
            x=0,
            line_dash="dash",
            line_color="#f85149",
            annotation_text="Zero / 零",
            annotation_font_color="#f85149",
        )

        apply_dark_theme(
            fig_carry,
            xaxis_title="Carry Efficiency / 息差效率 (%/yr)",
            yaxis_title="Count / 数量",
            barmode="overlay",
            height=350,
            margin=dict(l=60, r=20, t=20, b=60),
            legend=dict(
                orientation="h",
                yanchor="top",
                y=-0.2,
                xanchor="center",
                x=0.5,
                bgcolor="rgba(22, 27, 34, 0.8)",
                bordercolor="#30363d",
                font=dict(color="#e6edf3"),
            ),
        )

        st.plotly_chart(fig_carry, use_container_width=True)

    # ============================================
    # TAB 3: EXECUTIVE BRIEF
    # ============================================
    with tab3:
        brief_col1, brief_col2 = st.columns([2, 1])

        with brief_col1:
            st.markdown(f'<div class="section-header">📄 Executive Summary / 管理摘要</div>', unsafe_allow_html=True)

            if st.button(f"🔄 {LABELS['generate_summary']}", type="primary"):
                with st.spinner(LABELS["loading"]):
                    summary = filtered_analyzer.generate_executive_summary()
                    st.markdown(summary)

                    st.download_button(
                        label=f"📥 {LABELS['download_summary']}",
                        data=summary,
                        file_name="portfolio_summary.md",
                        mime="text/markdown",
                    )

        with brief_col2:
            st.markdown(f'<div class="section-header">{LABELS["sector_allocation"]}</div>', unsafe_allow_html=True)

            # Donut chart for sector allocation
            sector_values = list(metrics.sector_exposures.values())
            sector_names = [f"{k} / {SECTOR_NAMES_CN.get(k, k)}" for k in metrics.sector_exposures.keys()]
            sector_colors = [DARK_SECTOR_COLORS.get(k, "#6e7681") for k in metrics.sector_exposures.keys()]

            fig_sector = go.Figure(data=[go.Pie(
                labels=sector_names,
                values=sector_values,
                hole=0.5,
                marker_colors=sector_colors,
                textinfo="percent",
                textfont=dict(color="#e6edf3", size=10),
                hovertemplate="<b>%{label}</b><br>%{value:$,.0f}<br>%{percent}<extra></extra>",
            )])

            apply_dark_theme(
                fig_sector,
                height=300,
                margin=dict(l=20, r=20, t=20, b=20),
                showlegend=False,
            )

            st.plotly_chart(fig_sector, use_container_width=True)

        # Data Export Section
        st.markdown(f'<div class="section-header">📥 {LABELS["data_export"]}</div>', unsafe_allow_html=True)

        export_col1, export_col2, export_col3 = st.columns(3)

        with export_col1:
            csv_buffer = io.StringIO()
            df_filtered.to_csv(csv_buffer, index=False)
            st.download_button(
                label=f"📊 Full Portfolio / 完整组合 (CSV)",
                data=csv_buffer.getvalue(),
                file_name="portfolio_full.csv",
                mime="text/csv",
            )

        with export_col2:
            if len(sell_candidates) > 0:
                sell_csv = io.StringIO()
                sell_candidates.to_csv(sell_csv, index=False)
                st.download_button(
                    label=f"🔴 Sell List / 卖出清单 (CSV)",
                    data=sell_csv.getvalue(),
                    file_name="sell_candidates.csv",
                    mime="text/csv",
                )

        with export_col3:
            regression_results = filtered_analyzer.get_regression_results()
            if regression_results:
                reg_data = [r.to_dict() for r in regression_results.values()]
                reg_df = pd.DataFrame(reg_data)
                reg_csv = io.StringIO()
                reg_df.to_csv(reg_csv, index=False)
                st.download_button(
                    label=f"📈 Regression / 回归统计 (CSV)",
                    data=reg_csv.getvalue(),
                    file_name="regression_stats.csv",
                    mime="text/csv",
                )


if __name__ == "__main__":
    main()
