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
import logging
from pathlib import Path
from typing import Optional
import importlib

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

# Initialize logger
logger = logging.getLogger(__name__)

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent))

# Force reload of modules during development to avoid cache issues
from src.utils import constants as utils_constants
from src.module_b import data_loader as module_data_loader
from src.module_b import analytics as module_analytics
from src.module_b import financials as module_financials

importlib.reload(utils_constants)
importlib.reload(module_data_loader)
importlib.reload(module_analytics)
importlib.reload(module_financials)

from src.module_b.data_loader import DataLoader, DataValidationError
from src.module_b.analytics import PortfolioAnalyzer
from src.module_b.financials import FinancialDataLoader
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
        --bg-primary: #121212;
        --bg-secondary: #161b22;
        --bg-tertiary: #21262d;
        --bg-card: rgba(33, 38, 45, 0.85);
        --border-color: #30363d;
        --border-accent: #58a6ff;
        --text-primary: #e6edf3;
        --text-secondary: #8b949e;
        --text-muted: #6e7681;
        --accent-blue: #00B0FF;
        --accent-orange: #FF9800;
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
    .metric-card.accent-orange { border-left: 3px solid var(--accent-orange); }
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

    /* ====== LANGUAGE TOGGLE ====== */
    .lang-toggle {
        display: inline-block;
        background: var(--bg-tertiary);
        border: 1px solid var(--border-color);
        border-radius: 8px;
        padding: 0.25rem 0.75rem;
        font-size: 0.875rem;
        color: var(--text-secondary);
        cursor: pointer;
        transition: all 0.2s ease;
        margin-left: 1rem;
    }

    .lang-toggle:hover {
        border-color: var(--accent-orange);
        color: var(--accent-orange);
    }

    .lang-toggle.active {
        background: linear-gradient(135deg, var(--accent-orange) 0%, var(--accent-blue) 100%);
        color: white;
        border-color: var(--accent-orange);
    }

    /* ====== CREDIT INSPECTOR ====== */
    .inspector-header {
        font-size: 1.125rem;
        font-weight: 600;
        color: var(--accent-orange);
        margin: 1.5rem 0 1rem 0;
        padding: 0.5rem 0;
        border-bottom: 2px solid var(--accent-orange);
        font-family: var(--font-mono);
    }

    .inspector-subheader {
        font-size: 0.875rem;
        color: var(--text-secondary);
        margin-bottom: 1rem;
        font-style: italic;
    }

    .fundamental-panel {
        background: var(--bg-card);
        border: 1px solid var(--border-color);
        border-left: 3px solid var(--accent-blue);
        border-radius: 8px;
        padding: 1rem;
        margin-bottom: 1rem;
    }

    .fundamental-title {
        font-size: 0.875rem;
        color: var(--accent-blue);
        text-transform: uppercase;
        letter-spacing: 0.05em;
        font-weight: 600;
        margin-bottom: 0.75rem;
    }

    .issuer-info {
        font-size: 0.8rem;
        color: var(--text-secondary);
        margin-bottom: 0.5rem;
        font-family: var(--font-mono);
    }

    .issuer-info .ticker {
        color: var(--accent-orange);
        font-weight: 600;
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
    "tab_issuer360": "Issuer 360 / 发行人全景",
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

# Additional vibrant colors for unknown sectors (auto-assigned)
FALLBACK_COLORS = [
    "#ff7eb9",  # Pink
    "#7ee8fa",  # Cyan
    "#ffc65d",  # Orange
    "#96f2d7",  # Mint
    "#d0bfff",  # Lavender
    "#ffa94d",  # Peach
    "#74c0fc",  # Sky blue
    "#a9e34b",  # Lime
    "#ff8787",  # Coral
    "#da77f2",  # Purple
    "#4dabf7",  # Blue
    "#ffe066",  # Yellow
]

def get_sector_color(sector: str, sector_color_map: dict = None) -> str:
    """
    Get color for a sector with dynamic fallback for unknown sectors.

    Args:
        sector: Sector name
        sector_color_map: Existing color mapping dictionary (updated in-place)

    Returns:
        Hex color code
    """
    if sector_color_map is None:
        sector_color_map = {}

    # Check if color already assigned
    if sector in DARK_SECTOR_COLORS:
        return DARK_SECTOR_COLORS[sector]

    if sector in sector_color_map:
        return sector_color_map[sector]

    # Assign a new color from fallback pool
    used_colors = set(sector_color_map.values())
    available_colors = [c for c in FALLBACK_COLORS if c not in used_colors]

    if available_colors:
        new_color = available_colors[0]
    else:
        # If all fallback colors used, generate a random one
        import random
        hue = random.randint(0, 360)
        new_color = f"hsl({hue}, 70%, 60%)"

    sector_color_map[sector] = new_color
    return new_color


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
    # Initialize session state FIRST (before any UI elements that depend on it)
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
    if "language" not in st.session_state:
        st.session_state.language = "EN"  # Default to English
    if "financial_loader" not in st.session_state:
        st.session_state.financial_loader = None
    if "fundamentals_loaded" not in st.session_state:
        st.session_state.fundamentals_loaded = False

    # Initialize dynamic sector color map in session state
    if "sector_color_map" not in st.session_state:
        st.session_state.sector_color_map = {}

    # Inject dark theme CSS
    st.markdown(DARK_THEME_CSS, unsafe_allow_html=True)

    # Header with Language Toggle
    header_col1, header_col2 = st.columns([4, 1])

    with header_col1:
        st.markdown(f'<h1 class="main-header">{LABELS["app_title"]}</h1>', unsafe_allow_html=True)
        st.markdown(f'<p class="sub-header">{LABELS["app_subtitle"]}</p>', unsafe_allow_html=True)

    with header_col2:
        # Language toggle button
        lang_button = st.button(
            f"🌐 {st.session_state.language}",
            key="lang_toggle",
            help="Switch Language / 切换语言"
        )
        if lang_button:
            st.session_state.language = "CN" if st.session_state.language == "EN" else "EN"
            st.rerun()

    # ============================================
    # FILTERS (Main Page Expander for Mobile)
    # ============================================
    # Auto-expand filter settings on first visit (when no data loaded)
    expand_filters = not st.session_state.data_loaded

    with st.expander(f"⚙️ {LABELS['filter_settings']}", expanded=expand_filters):
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
    # Auto-load sample data on first visit if no data is loaded yet
    if not st.session_state.data_loaded and not uploaded_file:
        use_sample = True

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

    # Load financial fundamentals data (one-time load)
    if not st.session_state.fundamentals_loaded:
        try:
            financial_loader = FinancialDataLoader()
            if financial_loader.load_data():
                st.session_state.financial_loader = financial_loader
                st.session_state.fundamentals_loaded = True
                coverage_stats = financial_loader.get_coverage_stats()
                logger.info(
                    f"Loaded fundamentals for {coverage_stats['bonds_with_fundamentals']} "
                    f"out of {coverage_stats['total_bonds']} bonds "
                    f"({coverage_stats['coverage_rate']*100:.1f}% coverage)"
                )
        except Exception as e:
            logger.warning(f"Could not load financial fundamentals: {e}")
            # Continue without fundamentals
            st.session_state.fundamentals_loaded = True  # Mark as attempted

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
    tab1, tab2, tab3, tab4 = st.tabs([
        f"📈 {LABELS['tab_matrix']}",
        f"🔬 {LABELS['tab_optimization']}",
        f"🏢 {LABELS['tab_issuer360']}",
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

            color = get_sector_color(sector, st.session_state.sector_color_map)
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

            # ============================================
            # TOTAL RETURN ANALYSIS
            # ============================================
            st.markdown("**📈 Total Return Analysis / 总回报分析**")
            st.markdown("*Rolldown, Carry, and Breakeven Spread Analysis / 滚动收益、息差及盈亏平衡分析*")

            # Calculate total return analysis
            total_return = filtered_analyzer.calculate_total_return_analysis(selected_ticker)

            if total_return is not None:
                # Create waterfall chart showing return components
                return_col1, return_col2 = st.columns([2, 1])

                with return_col1:
                    # Waterfall chart data
                    categories = [
                        "Current Yield<br>当前收益率",
                        "Rolldown Effect<br>滚动效应",
                        "Funding Cost<br>资金成本",
                        "Net Return<br>净回报"
                    ]

                    # Values for waterfall
                    yield_val = total_return.current_yield * 100
                    rolldown_val = total_return.rolldown_price_return * 100
                    funding_val = -total_return.funding_cost * 100  # Negative for cost
                    net_return_val = (total_return.current_yield + total_return.rolldown_price_return - total_return.funding_cost) * 100

                    # Measure types for waterfall
                    measure = ["relative", "relative", "relative", "total"]

                    # Colors
                    colors = ["#3fb950", "#58a6ff", "#f85149", "#a371f7"]

                    fig_waterfall = go.Figure(go.Waterfall(
                        name="Return Components",
                        orientation="v",
                        measure=measure,
                        x=categories,
                        y=[yield_val, rolldown_val, funding_val, net_return_val],
                        textposition="outside",
                        text=[f"{yield_val:.2f}%", f"{rolldown_val:+.2f}%", f"{funding_val:.2f}%", f"{net_return_val:.2f}%"],
                        textfont=dict(color="#e6edf3", size=11),
                        connector={"line": {"color": "#30363d", "width": 1}},
                        decreasing={"marker": {"color": "#f85149"}},
                        increasing={"marker": {"color": "#3fb950"}},
                        totals={"marker": {"color": "#a371f7"}},
                    ))

                    apply_dark_theme(
                        fig_waterfall,
                        title="Return Decomposition / 回报分解",
                        yaxis_title="Return / 回报 (%)",
                        height=350,
                        margin=dict(l=60, r=20, t=60, b=80),
                        showlegend=False,
                    )

                    st.plotly_chart(fig_waterfall, use_container_width=True)

                with return_col2:
                    # Safety Buffer / Breakeven Spread Metric
                    breakeven_bps = total_return.breakeven_spread_bps

                    # Determine color based on safety level
                    if breakeven_bps >= 50:
                        buffer_accent = "green"
                        buffer_status = "✅ Safe / 安全"
                    elif breakeven_bps >= 20:
                        buffer_accent = "yellow"
                        buffer_status = "⚠️ Moderate / 中等"
                    else:
                        buffer_accent = "red"
                        buffer_status = "🔴 At Risk / 风险"

                    st.markdown(render_metric_card(
                        "Breakeven Spread / 盈亏平衡",
                        f"{breakeven_bps:.0f} bps",
                        buffer_status,
                        "positive" if breakeven_bps >= 50 else "neutral" if breakeven_bps >= 20 else "negative",
                        buffer_accent
                    ), unsafe_allow_html=True)

                    st.markdown(render_metric_card(
                        "Net Carry / 净息差",
                        f"{total_return.net_carry * 100:.2f}%",
                        f"vs FTP: {total_return.funding_cost * 100:.2f}%",
                        "positive" if total_return.net_carry > 0 else "negative",
                        "green" if total_return.net_carry > 0 else "red"
                    ), unsafe_allow_html=True)

                    st.markdown(render_metric_card(
                        "Rolldown (1Y) / 滚动效应",
                        f"{total_return.rolldown_price_return * 100:+.2f}%",
                        f"D: {total_return.current_duration:.1f}y → {total_return.rolled_duration:.1f}y",
                        "positive" if total_return.rolldown_price_return > 0 else "negative",
                        "blue"
                    ), unsafe_allow_html=True)

                # Detailed breakdown table
                with st.expander("📊 Detailed Return Breakdown / 详细回报分解"):
                    breakdown_data = {
                        "Component / 组成部分": [
                            "Current Yield / 当前收益率",
                            "Model Yield (at Duration) / 模型收益率",
                            "Rolled Yield (D-1) / 滚动后收益率",
                            "Yield Change (Rolldown) / 收益率变化",
                            "Rolldown Price Return / 滚动价格回报",
                            "Funding Cost (FTP) / 资金成本",
                            "Net Carry / 净息差",
                            "Total Expected Return / 预期总回报",
                            "Breakeven Spread / 盈亏平衡利差"
                        ],
                        "Value / 数值": [
                            f"{total_return.current_yield * 100:.3f}%",
                            f"{total_return.current_model_yield * 100:.3f}%",
                            f"{total_return.rolled_model_yield * 100:.3f}%",
                            f"{total_return.rolldown_yield_change * 100:+.3f}%",
                            f"{total_return.rolldown_price_return * 100:+.3f}%",
                            f"{total_return.funding_cost * 100:.3f}%",
                            f"{total_return.net_carry * 100:+.3f}%",
                            f"{total_return.total_expected_return * 100:.3f}%",
                            f"{total_return.breakeven_spread_bps:.1f} bps"
                        ],
                        "Explanation / 说明": [
                            "Actual bond yield / 实际债券收益率",
                            "Fitted curve yield at current duration / 当前久期的拟合曲线收益率",
                            "Fitted curve yield at duration - 1 year / 久期减1年后的拟合曲线收益率",
                            "Change in yield from rolling down curve / 沿曲线滚动的收益率变化",
                            "≈ -Duration × Yield Change / 约等于 -久期 × 收益率变化",
                            "Transfer pricing rate / 资金转移定价利率",
                            "Yield - Funding Cost / 收益率 - 资金成本",
                            "Yield + Rolldown Effect / 收益率 + 滚动效应",
                            "Net Carry ÷ Duration (safety buffer) / 净息差 ÷ 久期 (安全缓冲)"
                        ]
                    }
                    st.dataframe(pd.DataFrame(breakdown_data), use_container_width=True, hide_index=True)

                    st.markdown("""
                    **Interpretation / 解释:**
                    - **Breakeven Spread** tells you how much credit spreads can widen before your 1-year carry is wiped out
                    - **盈亏平衡利差**表示信用利差可以扩大多少，才会抵消1年的息差收益
                    - Higher breakeven = more safety margin / 更高的盈亏平衡 = 更大的安全边际
                    """)
            else:
                st.warning("Unable to calculate total return analysis. Curve may not be fitted for this sector.")
                st.warning("无法计算总回报分析。该板块可能没有拟合曲线。")

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
                    marker_color = "#FFD700" if is_selected else get_sector_color(row["Sector_L1"], st.session_state.sector_color_map)
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
                            line=dict(color=get_sector_color(sector, st.session_state.sector_color_map), width=2, dash="dash"),
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

            # ============================================
            # CREDIT INSPECTOR (FUNDAMENTALS)
            # ============================================
            st.markdown('<div class="inspector-header">🔍 Credit Inspector / 信用分析</div>', unsafe_allow_html=True)
            st.markdown('<div class="inspector-subheader">Combining Pricing Signals & Financial Fundamentals / 结合定价信号与财务基本面</div>', unsafe_allow_html=True)

            inspector_col1, inspector_col2 = st.columns([1, 1])

            # LEFT COLUMN: Pricing Summary
            with inspector_col1:
                st.markdown('<div class="fundamental-panel">', unsafe_allow_html=True)
                st.markdown('<div class="fundamental-title">📊 Pricing Analysis / 定价分析</div>', unsafe_allow_html=True)

                # Display pricing metrics (already calculated above)
                pricing_summary_col1, pricing_summary_col2 = st.columns(2)

                with pricing_summary_col1:
                    st.markdown(render_metric_card(
                        "Fair Value / 公允价值",
                        format_percentage(bond_data.get("Model_Yield", bond_data["Yield"])),
                        "NS Model / NS模型",
                        "neutral",
                        "blue"
                    ), unsafe_allow_html=True)

                with pricing_summary_col2:
                    z_class = get_z_score_class(bond_data["Z_Score"])
                    z_accent = "red" if z_class == "rich" else "green" if z_class == "cheap" else "yellow"
                    st.markdown(render_metric_card(
                        "Valuation / 估值",
                        get_z_score_label(bond_data["Z_Score"]),
                        f"Z-Score: {bond_data['Z_Score']:.2f}" if not pd.isna(bond_data['Z_Score']) else "N/A",
                        "neutral",
                        z_accent
                    ), unsafe_allow_html=True)

                st.markdown('</div>', unsafe_allow_html=True)

            # RIGHT COLUMN: Financial Fundamentals
            with inspector_col2:
                st.markdown('<div class="fundamental-panel">', unsafe_allow_html=True)
                st.markdown('<div class="fundamental-title">💼 Financial Fundamentals / 财务基本面</div>', unsafe_allow_html=True)

                # Get fundamental data
                if st.session_state.financial_loader is not None:
                    fundamentals = st.session_state.financial_loader.get_issuer_fundamentals(selected_ticker)

                    if fundamentals is not None:
                        latest = fundamentals.latest_quarter

                        # Display issuer information
                        st.markdown(
                            f'<div class="issuer-info">'
                            f'<span class="ticker">{fundamentals.equity_ticker}</span> | {fundamentals.issuer_name}'
                            f'</div>',
                            unsafe_allow_html=True
                        )

                        if latest is not None:
                            # KPI Cards for latest quarter
                            kpi_col1, kpi_col2, kpi_col3 = st.columns(3)

                            with kpi_col1:
                                rev_growth = latest.revenue_qoq_growth
                                rev_growth_str = f"{rev_growth*100:+.1f}%" if rev_growth is not None else "N/A"
                                rev_delta_type = "positive" if (rev_growth and rev_growth > 0) else "negative" if rev_growth else "neutral"

                                st.markdown(render_metric_card(
                                    "Rev Growth QoQ<br>收入增长",
                                    rev_growth_str,
                                    f"{latest.year}Q{latest.quarter}",
                                    rev_delta_type,
                                    "green" if (rev_growth and rev_growth > 0) else "red" if rev_growth else "orange"
                                ), unsafe_allow_html=True)

                            with kpi_col2:
                                leverage = latest.net_leverage
                                leverage_str = f"{leverage:.2f}x" if leverage is not None else "N/A"
                                leverage_accent = "red" if (leverage and leverage > 5) else "yellow" if (leverage and leverage > 3) else "green"

                                st.markdown(render_metric_card(
                                    "Net Leverage<br>净杠杆",
                                    leverage_str,
                                    "ND/EBITDA",
                                    "neutral",
                                    leverage_accent
                                ), unsafe_allow_html=True)

                            with kpi_col3:
                                coverage = latest.interest_coverage
                                coverage_str = f"{coverage:.1f}x" if coverage is not None else "N/A"
                                coverage_accent = "green" if (coverage and coverage > 3) else "yellow" if (coverage and coverage > 1.5) else "red"

                                st.markdown(render_metric_card(
                                    "Int Coverage<br>利息覆盖",
                                    coverage_str,
                                    "EBITDA/Int",
                                    "neutral",
                                    coverage_accent
                                ), unsafe_allow_html=True)

                            # Trend Chart (8 quarters)
                            st.markdown("**📈 Leverage Trend / 杠杆趋势 (8Q)**")

                            dates, values = fundamentals.get_trend_series('net_leverage')

                            if dates and values:
                                fig_fundamental = go.Figure()

                                fig_fundamental.add_trace(go.Scatter(
                                    x=dates,
                                    y=values,
                                    mode='lines+markers',
                                    fill='tozeroy',
                                    line=dict(color='#00B0FF', width=2),
                                    marker=dict(size=6, color='#00B0FF'),
                                    name='Net Leverage',
                                    hovertemplate='<b>%{x}</b><br>Leverage: %{y:.2f}x<extra></extra>'
                                ))

                                apply_dark_theme(
                                    fig_fundamental,
                                    xaxis_title="Quarter / 季度",
                                    yaxis_title="Net Leverage (x)",
                                    height=250,
                                    margin=dict(l=40, r=20, t=20, b=40),
                                    showlegend=False,
                                )

                                # Remove grid lines for minimalist look
                                fig_fundamental.update_xaxes(showgrid=False)
                                fig_fundamental.update_yaxes(showgrid=True, gridcolor="rgba(48, 54, 61, 0.2)")

                                st.plotly_chart(fig_fundamental, use_container_width=True)
                            else:
                                st.info("Insufficient data for trend chart / 趋势数据不足")

                        else:
                            st.info("No quarterly data available / 无季度数据")
                    else:
                        st.info("No fundamental data available for this issuer / 该发行人无基本面数据")
                        st.markdown("*Fundamentals are linked via equity ticker mapping*")
                        st.markdown("*基本面数据通过股票代码映射*")
                else:
                    st.warning("Financial data module not loaded / 财务数据模块未加载")

                st.markdown('</div>', unsafe_allow_html=True)

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

            color = get_sector_color(sector, st.session_state.sector_color_map)

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
    # TAB 3: ISSUER 360 DASHBOARD
    # ============================================
    with tab3:
        st.markdown(f'<div class="section-header">🏢 Issuer 360 / 发行人全景</div>', unsafe_allow_html=True)
        st.markdown("*Comprehensive issuer analysis: Market Data (Yield Curve) + Fundamental Data (Financials vs. Peers)*")
        st.markdown("*综合发行人分析：市场数据（收益率曲线）+ 基本面数据（财务与同业比较）*")

        # ============================================
        # ISSUER SELECTION
        # ============================================
        issuer_select_col1, issuer_select_col2 = st.columns([3, 1])

        with issuer_select_col1:
            # Get unique issuers from bond_equity_map
            if st.session_state.financial_loader is not None and st.session_state.financial_loader.bond_equity_map is not None:
                bond_equity_map = st.session_state.financial_loader.bond_equity_map
                # Filter to only issuers with data
                available_issuers = bond_equity_map[
                    bond_equity_map['Bond_Ticker'].isin(df_filtered['Ticker'].str.split().str[0])
                ].copy()

                # Create issuer display names
                available_issuers['Display_Name'] = available_issuers['Issuer_Name'] + " (" + available_issuers['Bond_Ticker'] + ")"
                issuer_options = sorted(available_issuers['Display_Name'].unique())

                selected_issuer_display = st.selectbox(
                    "Select Issuer / 选择发行人",
                    options=[""] + issuer_options,
                    format_func=lambda x: "-- Select an issuer --" if x == "" else x,
                    key="issuer_360_selector"
                )
            else:
                st.warning("Financial data not loaded. Please check data files.")
                st.warning("财务数据未加载，请检查数据文件。")
                selected_issuer_display = ""

        with issuer_select_col2:
            st.markdown("**Quick Stats / 快速统计**")
            if selected_issuer_display:
                # Extract bond ticker from display name
                selected_issuer_ticker = selected_issuer_display.split("(")[-1].rstrip(")")
                issuer_bonds = df_filtered[df_filtered["Ticker"].str.startswith(selected_issuer_ticker)]
                st.metric("Bonds in Portfolio / 组合中债券数", len(issuer_bonds))
                st.metric("Total Exposure / 总敞口", format_currency(issuer_bonds['Nominal_USD'].sum()))

        if selected_issuer_display and selected_issuer_display != "":
            # Extract issuer info
            selected_issuer_ticker = selected_issuer_display.split("(")[-1].rstrip(")")
            selected_issuer_row = available_issuers[available_issuers['Bond_Ticker'] == selected_issuer_ticker].iloc[0]
            selected_issuer_name = selected_issuer_row['Issuer_Name']
            selected_equity_ticker = selected_issuer_row['Equity_Ticker']

            # Get issuer sector from first bond
            issuer_bonds_all = df_filtered[df_filtered["Ticker"].str.startswith(selected_issuer_ticker)]
            if len(issuer_bonds_all) > 0:
                issuer_sector = issuer_bonds_all.iloc[0]['Sector_L1']
            else:
                issuer_sector = None

            st.markdown("---")

            # ============================================
            # SECTION A: VALUATION CURVE (Issuer vs. Sector)
            # ============================================
            st.markdown(f'<div class="section-header">📊 Section A: Valuation Curve / 估值曲线分析</div>', unsafe_allow_html=True)
            st.markdown(f"**{selected_issuer_name}** bonds vs. **{issuer_sector}** sector curve")
            st.markdown(f"**{selected_issuer_name}** 债券 vs. **{issuer_sector}** 板块曲线")

            curve_col1, curve_col2 = st.columns([3, 1])

            with curve_col1:
                # Create scatter + line chart
                fig_issuer_curve = go.Figure()

                # Get all bonds from this issuer
                issuer_bonds = df_filtered[df_filtered["Ticker"].str.startswith(selected_issuer_ticker)]

                if len(issuer_bonds) > 0:
                    # Plot issuer bonds as gold scatter points
                    hover_text_issuer = issuer_bonds.apply(
                        lambda row: (
                            f"<b>{row['Ticker']}</b><br>"
                            f"名称: {row.get('Name', 'N/A')}<br>"
                            f"━━━━━━━━━━━━<br>"
                            f"YTM: {row['Yield']*100:.2f}%<br>"
                            f"Duration: {row['Duration']:.2f}y<br>"
                            f"OAS: {row['OAS']:.0f}bp<br>"
                            f"Z-Score: {row['Z_Score']:.2f}<br>"
                            f"━━━━━━━━━━━━<br>"
                            f"Notional: {format_currency(row['Nominal_USD'])}"
                        ),
                        axis=1,
                    )

                    sizes_issuer = np.clip(issuer_bonds["Nominal_USD"] / 1e6, 8, 30)

                    fig_issuer_curve.add_trace(go.Scatter(
                        x=issuer_bonds["Duration"],
                        y=issuer_bonds["Yield"] * 100,
                        mode="markers",
                        name=f"{selected_issuer_ticker} Bonds",
                        marker=dict(
                            size=sizes_issuer,
                            color="#FFD700",  # Gold
                            opacity=0.9,
                            line=dict(width=2, color="white"),
                            symbol="diamond"
                        ),
                        hovertemplate="%{hovertext}<extra></extra>",
                        hovertext=hover_text_issuer,
                    ))

                    # Line 1: Issuer Curve (if more than 2 bonds)
                    if len(issuer_bonds) >= 3:
                        try:
                            from scipy.interpolate import interp1d
                            x_issuer = issuer_bonds["Duration"].values
                            y_issuer = issuer_bonds["Yield"].values

                            # Sort by duration
                            sort_idx = np.argsort(x_issuer)
                            x_issuer = x_issuer[sort_idx]
                            y_issuer = y_issuer[sort_idx]

                            # Linear interpolation
                            f_issuer = interp1d(x_issuer, y_issuer, kind='linear', fill_value='extrapolate')
                            x_curve_issuer = np.linspace(x_issuer.min(), x_issuer.max(), 50)
                            y_curve_issuer = f_issuer(x_curve_issuer)

                            fig_issuer_curve.add_trace(go.Scatter(
                                x=x_curve_issuer,
                                y=y_curve_issuer * 100,
                                mode="lines",
                                name=f"{selected_issuer_ticker} Curve",
                                line=dict(color="#FFD700", width=3, dash="solid"),
                                hoverinfo="skip",
                            ))
                        except Exception as e:
                            logger.warning(f"Could not fit issuer curve: {e}")

                    # Line 2: Sector Benchmark (Nelson-Siegel curve)
                    if issuer_sector and issuer_sector in filtered_analyzer.get_regression_results():
                        try:
                            x_sector, y_sector = filtered_analyzer.get_curve_points(issuer_sector, n_points=50)
                            sector_color = get_sector_color(issuer_sector, st.session_state.sector_color_map)

                            fig_issuer_curve.add_trace(go.Scatter(
                                x=x_sector,
                                y=y_sector * 100,
                                mode="lines",
                                name=f"{issuer_sector} Sector Curve",
                                line=dict(color=sector_color, width=3, dash="dash"),
                                hoverinfo="skip",
                            ))
                        except Exception as e:
                            logger.warning(f"Could not get sector curve: {e}")

                    apply_dark_theme(
                        fig_issuer_curve,
                        xaxis_title="Duration / 久期 (Years)",
                        yaxis_title="YTM / 到期收益率 (%)",
                        hovermode="closest",
                        height=450,
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

                    st.plotly_chart(fig_issuer_curve, use_container_width=True)
                else:
                    st.info("No bonds found for this issuer in the current portfolio.")
                    st.info("当前组合中未找到该发行人的债券。")

            with curve_col2:
                st.markdown("**📈 Insight / 洞察**")
                if len(issuer_bonds) > 0:
                    avg_z_score = issuer_bonds['Z_Score'].mean()
                    if avg_z_score < -1.0:
                        st.markdown("🔴 **Trading WIDE (Rich) / 偏贵**")
                        st.markdown("Yields are LOWER than sector average")
                        st.markdown("收益率低于板块平均水平")
                        st.markdown(f"Avg Z-Score: {avg_z_score:.2f}")
                    elif avg_z_score > 1.0:
                        st.markdown("🟢 **Trading TIGHT (Cheap) / 偏便宜**")
                        st.markdown("Yields are HIGHER than sector average")
                        st.markdown("收益率高于板块平均水平")
                        st.markdown(f"Avg Z-Score: {avg_z_score:.2f}")
                    else:
                        st.markdown("🟡 **Fair Value / 公允估值**")
                        st.markdown("Trading in line with sector")
                        st.markdown("与板块走势一致")
                        st.markdown(f"Avg Z-Score: {avg_z_score:.2f}")

                    st.markdown("---")
                    st.markdown("**Portfolio Holdings / 组合持仓**")
                    st.metric("Total Bonds / 债券总数", len(issuer_bonds))
                    st.metric("Weighted Duration / 加权久期", f"{(issuer_bonds['Duration'] * issuer_bonds['Nominal_USD']).sum() / issuer_bonds['Nominal_USD'].sum():.2f}y")
                    st.metric("Weighted YTM / 加权收益率", f"{(issuer_bonds['Yield'] * issuer_bonds['Nominal_USD']).sum() / issuer_bonds['Nominal_USD'].sum() * 100:.2f}%")

            st.markdown("---")

            # ============================================
            # SECTION B: FINANCIAL DASHBOARD (2x2 Grid)
            # ============================================
            st.markdown(f'<div class="section-header">💼 Section B: Financial Dashboard / 财务仪表板</div>', unsafe_allow_html=True)
            st.markdown("*Quarterly trend analysis across key credit metrics*")
            st.markdown("*关键信用指标的季度趋势分析*")

            # Get fundamentals for this issuer
            if st.session_state.financial_loader is not None:
                fundamentals = st.session_state.financial_loader.get_issuer_fundamentals(selected_issuer_ticker)

                if fundamentals is not None:
                    # Get last 8 quarters
                    quarters = fundamentals.last_8_quarters

                    if len(quarters) > 0:
                        # Create 2x2 grid
                        fin_row1_col1, fin_row1_col2 = st.columns(2)
                        fin_row2_col1, fin_row2_col2 = st.columns(2)

                        # CHART 1: Deleveraging (Bar: Total Liabilities + Line: Net Leverage)
                        with fin_row1_col1:
                            st.markdown("**📉 Deleveraging / 去杠杆**")

                            dates, liabilities_vals = fundamentals.get_trend_series('total_liabilities')
                            _, leverage_vals = fundamentals.get_trend_series('net_leverage')

                            fig_delever = go.Figure()

                            # Bar chart for Total Liabilities
                            fig_delever.add_trace(go.Bar(
                                x=dates,
                                y=[v/1e9 for v in liabilities_vals],  # Convert to billions
                                name='Total Liabilities',
                                marker_color='#58a6ff',
                                yaxis='y',
                                hovertemplate='<b>%{x}</b><br>Total Liabilities: $%{y:.2f}B<extra></extra>'
                            ))

                            # Line chart for Net Leverage (right axis)
                            if len(leverage_vals) > 0:
                                fig_delever.add_trace(go.Scatter(
                                    x=dates[-len(leverage_vals):],
                                    y=leverage_vals,
                                    name='Net Leverage',
                                    mode='lines+markers',
                                    line=dict(color='#f85149', width=3),
                                    marker=dict(size=8, color='#f85149'),
                                    yaxis='y2',
                                    hovertemplate='<b>%{x}</b><br>Net Leverage: %{y:.2f}x<extra></extra>'
                                ))

                            fig_delever.update_layout(
                                yaxis=dict(title='Total Liabilities ($B)', side='left', color='#58a6ff'),
                                yaxis2=dict(title='Net Leverage (x)', side='right', overlaying='y', color='#f85149'),
                                hovermode='x unified',
                                height=280,
                                margin=dict(l=50, r=50, t=20, b=40),
                                showlegend=True,
                                legend=dict(orientation="h", yanchor="top", y=-0.2, xanchor="center", x=0.5)
                            )

                            apply_dark_theme(fig_delever)
                            st.plotly_chart(fig_delever, use_container_width=True)

                        # CHART 2: Liquidity (Stacked Area: Cash vs. Net Interest Expense)
                        with fin_row1_col2:
                            st.markdown("**💰 Liquidity / 流动性**")

                            _, cash_vals = fundamentals.get_trend_series('cash')
                            _, int_exp_vals = fundamentals.get_trend_series('net_int_exp')

                            fig_liquidity = go.Figure()

                            # Stacked area for Cash
                            fig_liquidity.add_trace(go.Scatter(
                                x=dates[-len(cash_vals):] if len(cash_vals) > 0 else [],
                                y=[v/1e9 for v in cash_vals] if len(cash_vals) > 0 else [],
                                name='Cash',
                                mode='lines',
                                fill='tozeroy',
                                line=dict(color='#3fb950', width=2),
                                hovertemplate='<b>%{x}</b><br>Cash: $%{y:.2f}B<extra></extra>'
                            ))

                            # Stacked area for Net Interest Expense
                            fig_liquidity.add_trace(go.Scatter(
                                x=dates[-len(int_exp_vals):] if len(int_exp_vals) > 0 else [],
                                y=[abs(v)/1e9 for v in int_exp_vals] if len(int_exp_vals) > 0 else [],
                                name='Net Int Exp',
                                mode='lines',
                                fill='tonexty',
                                line=dict(color='#f85149', width=2),
                                hovertemplate='<b>%{x}</b><br>Net Int Exp: $%{y:.2f}B<extra></extra>'
                            ))

                            fig_liquidity.update_layout(
                                yaxis_title='Amount ($B)',
                                hovermode='x unified',
                                height=280,
                                margin=dict(l=50, r=20, t=20, b=40),
                                showlegend=True,
                                legend=dict(orientation="h", yanchor="top", y=-0.2, xanchor="center", x=0.5)
                            )

                            apply_dark_theme(fig_liquidity)
                            st.plotly_chart(fig_liquidity, use_container_width=True)

                        # CHART 3: Profitability (Line: EBITDA Margin)
                        with fin_row2_col1:
                            st.markdown("**📊 Profitability / 盈利能力**")

                            # Calculate EBITDA margin for each quarter
                            ebitda_margins = []
                            dates_margin = []
                            for q in quarters:
                                if q.revenue > 0 and q.ebitda > 0:
                                    margin = (q.ebitda / q.revenue) * 100
                                    ebitda_margins.append(margin)
                                    dates_margin.append(f"{q.year}Q{q.quarter}")

                            fig_profit = go.Figure()

                            fig_profit.add_trace(go.Scatter(
                                x=dates_margin,
                                y=ebitda_margins,
                                name='EBITDA Margin',
                                mode='lines+markers',
                                line=dict(color='#a371f7', width=3),
                                marker=dict(size=8, color='#a371f7'),
                                fill='tozeroy',
                                hovertemplate='<b>%{x}</b><br>EBITDA Margin: %{y:.1f}%<extra></extra>'
                            ))

                            fig_profit.update_layout(
                                yaxis_title='EBITDA Margin (%)',
                                hovermode='x unified',
                                height=280,
                                margin=dict(l=50, r=20, t=20, b=40),
                                showlegend=False
                            )

                            apply_dark_theme(fig_profit)
                            st.plotly_chart(fig_profit, use_container_width=True)

                        # CHART 4: Growth (Bar: Revenue QoQ)
                        with fin_row2_col2:
                            st.markdown("**📈 Growth / 增长**")

                            dates_rev, revenue_vals = fundamentals.get_trend_series('revenue')

                            # Calculate QoQ growth
                            qoq_growth = []
                            dates_qoq = []
                            for i in range(1, len(revenue_vals)):
                                if revenue_vals[i-1] > 0:
                                    growth = ((revenue_vals[i] - revenue_vals[i-1]) / revenue_vals[i-1]) * 100
                                    qoq_growth.append(growth)
                                    dates_qoq.append(dates_rev[i])

                            fig_growth = go.Figure()

                            # Color bars based on positive/negative growth
                            colors = ['#3fb950' if g >= 0 else '#f85149' for g in qoq_growth]

                            fig_growth.add_trace(go.Bar(
                                x=dates_qoq,
                                y=qoq_growth,
                                name='Revenue QoQ Growth',
                                marker_color=colors,
                                hovertemplate='<b>%{x}</b><br>QoQ Growth: %{y:.1f}%<extra></extra>'
                            ))

                            # Add zero line
                            fig_growth.add_hline(y=0, line_dash="dash", line_color="#30363d", line_width=1)

                            fig_growth.update_layout(
                                yaxis_title='Revenue Growth (%)',
                                hovermode='x unified',
                                height=280,
                                margin=dict(l=50, r=20, t=20, b=40),
                                showlegend=False
                            )

                            apply_dark_theme(fig_growth)
                            st.plotly_chart(fig_growth, use_container_width=True)

                    else:
                        st.info("No quarterly financial data available for this issuer.")
                        st.info("该发行人无季度财务数据。")
                else:
                    st.info("No fundamental data available for this issuer.")
                    st.info("该发行人无基本面数据。")
            else:
                st.warning("Financial data module not loaded.")
                st.warning("财务数据模块未加载。")

            st.markdown("---")

            # ============================================
            # SECTION C: CREDIT PEERS (The "Killer Feature")
            # ============================================
            st.markdown(f'<div class="section-header">🎯 Section C: Credit Peers / 信用同业对比</div>', unsafe_allow_html=True)
            st.markdown("*Benchmarking against sector peers*")
            st.markdown("*与板块同业基准对比*")

            if issuer_sector and st.session_state.financial_loader is not None:
                # Get all issuers in the same sector
                sector_bonds = df_filtered[df_filtered["Sector_L1"] == issuer_sector]
                sector_issuers = sector_bonds["Ticker"].str.split().str[0].unique()

                # Get fundamentals for all peer issuers
                peer_metrics_list = []
                selected_issuer_metrics = None

                for peer_ticker in sector_issuers:
                    peer_fundamentals = st.session_state.financial_loader.get_issuer_fundamentals(peer_ticker)
                    if peer_fundamentals is not None:
                        latest = peer_fundamentals.latest_quarter
                        if latest is not None:
                            metrics_dict = {
                                'ticker': peer_ticker,
                                'issuer_name': peer_fundamentals.issuer_name,
                                'net_leverage': latest.net_leverage,
                                'interest_coverage': latest.interest_coverage,
                                'ebitda_margin': (latest.ebitda / latest.revenue * 100) if latest.revenue > 0 else None,
                                'cash_ratio': (latest.cash / latest.total_liabilities * 100) if latest.total_liabilities > 0 else None,
                                'revenue_growth': latest.revenue_qoq_growth * 100 if latest.revenue_qoq_growth is not None else None
                            }

                            if peer_ticker == selected_issuer_ticker:
                                selected_issuer_metrics = metrics_dict
                            else:
                                peer_metrics_list.append(metrics_dict)

                if len(peer_metrics_list) > 0 and selected_issuer_metrics is not None:
                    # Calculate peer averages
                    peer_avg = {
                        'net_leverage': np.nanmean([p['net_leverage'] for p in peer_metrics_list if p['net_leverage'] is not None]),
                        'interest_coverage': np.nanmean([p['interest_coverage'] for p in peer_metrics_list if p['interest_coverage'] is not None]),
                        'ebitda_margin': np.nanmean([p['ebitda_margin'] for p in peer_metrics_list if p['ebitda_margin'] is not None]),
                        'cash_ratio': np.nanmean([p['cash_ratio'] for p in peer_metrics_list if p['cash_ratio'] is not None]),
                        'revenue_growth': np.nanmean([p['revenue_growth'] for p in peer_metrics_list if p['revenue_growth'] is not None])
                    }

                    peer_col1, peer_col2 = st.columns([2, 1])

                    with peer_col1:
                        # Try radar chart first, fall back to bar chart if issues
                        try:
                            # Radar Chart (Spider Chart)
                            categories = [
                                'Int Coverage<br>利息覆盖',
                                'EBITDA Margin<br>EBITDA利润率',
                                'Cash Ratio<br>现金比率',
                                'Revenue Growth<br>收入增长',
                                'Net Leverage (Inv)<br>净杠杆（倒数）'
                            ]

                            # Prepare values (normalize where needed)
                            issuer_vals = [
                                selected_issuer_metrics['interest_coverage'] if selected_issuer_metrics['interest_coverage'] is not None else 0,
                                selected_issuer_metrics['ebitda_margin'] if selected_issuer_metrics['ebitda_margin'] is not None else 0,
                                selected_issuer_metrics['cash_ratio'] if selected_issuer_metrics['cash_ratio'] is not None else 0,
                                selected_issuer_metrics['revenue_growth'] if selected_issuer_metrics['revenue_growth'] is not None else 0,
                                (1 / selected_issuer_metrics['net_leverage'] * 10) if selected_issuer_metrics['net_leverage'] is not None and selected_issuer_metrics['net_leverage'] > 0 else 0
                            ]

                            peer_vals = [
                                peer_avg['interest_coverage'] if not np.isnan(peer_avg['interest_coverage']) else 0,
                                peer_avg['ebitda_margin'] if not np.isnan(peer_avg['ebitda_margin']) else 0,
                                peer_avg['cash_ratio'] if not np.isnan(peer_avg['cash_ratio']) else 0,
                                peer_avg['revenue_growth'] if not np.isnan(peer_avg['revenue_growth']) else 0,
                                (1 / peer_avg['net_leverage'] * 10) if not np.isnan(peer_avg['net_leverage']) and peer_avg['net_leverage'] > 0 else 0
                            ]

                            fig_radar = go.Figure()

                            # Peer average (gray line)
                            fig_radar.add_trace(go.Scatterpolar(
                                r=peer_vals,
                                theta=categories,
                                fill='toself',
                                name='Sector Average',
                                line=dict(color='#8b949e', width=2),
                                fillcolor='rgba(139, 148, 158, 0.2)',
                                hovertemplate='<b>%{theta}</b><br>Sector Avg: %{r:.2f}<extra></extra>'
                            ))

                            # Selected issuer (blue area)
                            fig_radar.add_trace(go.Scatterpolar(
                                r=issuer_vals,
                                theta=categories,
                                fill='toself',
                                name=selected_issuer_ticker,
                                line=dict(color='#58a6ff', width=3),
                                fillcolor='rgba(88, 166, 255, 0.3)',
                                hovertemplate='<b>%{theta}</b><br>' + selected_issuer_ticker + ': %{r:.2f}<extra></extra>'
                            ))

                            fig_radar.update_layout(
                                polar=dict(
                                    radialaxis=dict(
                                        visible=True,
                                        range=[0, max(max(issuer_vals), max(peer_vals)) * 1.2],
                                        gridcolor='#30363d',
                                        tickfont=dict(color='#8b949e')
                                    ),
                                    angularaxis=dict(
                                        gridcolor='#30363d',
                                        tickfont=dict(color='#e6edf3', size=10)
                                    ),
                                    bgcolor='rgba(22, 27, 34, 0.5)'
                                ),
                                showlegend=True,
                                legend=dict(
                                    orientation="h",
                                    yanchor="top",
                                    y=-0.1,
                                    xanchor="center",
                                    x=0.5,
                                    bgcolor="rgba(22, 27, 34, 0.8)",
                                    bordercolor="#30363d",
                                    font=dict(color="#e6edf3")
                                ),
                                height=400,
                                margin=dict(l=80, r=80, t=40, b=80),
                                paper_bgcolor="rgba(13, 17, 23, 0)",
                                plot_bgcolor="rgba(22, 27, 34, 0.5)",
                                font=dict(color="#e6edf3")
                            )

                            st.plotly_chart(fig_radar, use_container_width=True)

                        except Exception as e:
                            # Fallback to side-by-side bar chart
                            logger.warning(f"Could not create radar chart, using bar chart: {e}")

                            st.markdown("**Issuer vs. Peer Average Comparison**")
                            st.markdown("**发行人 vs. 同业平均对比**")

                            comparison_data = {
                                'Metric / 指标': [
                                    'Net Leverage / 净杠杆',
                                    'Interest Coverage / 利息覆盖',
                                    'EBITDA Margin / EBITDA利润率',
                                    'Cash Ratio / 现金比率',
                                    'Revenue Growth / 收入增长'
                                ],
                                'Issuer / 发行人': [
                                    f"{selected_issuer_metrics['net_leverage']:.2f}x" if selected_issuer_metrics['net_leverage'] is not None else "N/A",
                                    f"{selected_issuer_metrics['interest_coverage']:.2f}x" if selected_issuer_metrics['interest_coverage'] is not None else "N/A",
                                    f"{selected_issuer_metrics['ebitda_margin']:.1f}%" if selected_issuer_metrics['ebitda_margin'] is not None else "N/A",
                                    f"{selected_issuer_metrics['cash_ratio']:.1f}%" if selected_issuer_metrics['cash_ratio'] is not None else "N/A",
                                    f"{selected_issuer_metrics['revenue_growth']:.1f}%" if selected_issuer_metrics['revenue_growth'] is not None else "N/A"
                                ],
                                'Sector Avg / 板块平均': [
                                    f"{peer_avg['net_leverage']:.2f}x" if not np.isnan(peer_avg['net_leverage']) else "N/A",
                                    f"{peer_avg['interest_coverage']:.2f}x" if not np.isnan(peer_avg['interest_coverage']) else "N/A",
                                    f"{peer_avg['ebitda_margin']:.1f}%" if not np.isnan(peer_avg['ebitda_margin']) else "N/A",
                                    f"{peer_avg['cash_ratio']:.1f}%" if not np.isnan(peer_avg['cash_ratio']) else "N/A",
                                    f"{peer_avg['revenue_growth']:.1f}%" if not np.isnan(peer_avg['revenue_growth']) else "N/A"
                                ]
                            }

                            st.dataframe(pd.DataFrame(comparison_data), use_container_width=True, hide_index=True)

                    with peer_col2:
                        st.markdown("**📊 Peer Statistics / 同业统计**")
                        st.metric("Sector / 板块", issuer_sector)
                        st.metric("Peer Count / 同业数量", len(peer_metrics_list))
                        st.markdown("---")
                        st.markdown("**Key Takeaways / 关键结论**")

                        # Generate insights
                        insights = []
                        if selected_issuer_metrics['net_leverage'] is not None and not np.isnan(peer_avg['net_leverage']):
                            if selected_issuer_metrics['net_leverage'] < peer_avg['net_leverage']:
                                insights.append("✅ Lower leverage than peers / 杠杆低于同业")
                            else:
                                insights.append("⚠️ Higher leverage than peers / 杠杆高于同业")

                        if selected_issuer_metrics['interest_coverage'] is not None and not np.isnan(peer_avg['interest_coverage']):
                            if selected_issuer_metrics['interest_coverage'] > peer_avg['interest_coverage']:
                                insights.append("✅ Better interest coverage / 利息覆盖更好")
                            else:
                                insights.append("⚠️ Weaker interest coverage / 利息覆盖较弱")

                        if selected_issuer_metrics['ebitda_margin'] is not None and not np.isnan(peer_avg['ebitda_margin']):
                            if selected_issuer_metrics['ebitda_margin'] > peer_avg['ebitda_margin']:
                                insights.append("✅ Higher profitability / 盈利能力更强")
                            else:
                                insights.append("⚠️ Lower profitability / 盈利能力较弱")

                        for insight in insights:
                            st.markdown(f"- {insight}")

                        if len(insights) == 0:
                            st.info("Insufficient data for comparison")
                            st.info("对比数据不足")

                else:
                    st.info(f"No peer data available for sector {issuer_sector}")
                    st.info(f"板块 {issuer_sector} 无同业数据")
            else:
                st.warning("Cannot perform peer analysis without sector information or financial data.")
                st.warning("缺少板块信息或财务数据，无法进行同业分析。")

        else:
            st.info("☝️ Select an issuer above to see comprehensive analysis / 选择上方的发行人查看综合分析")

    # ============================================
    # TAB 4: EXECUTIVE BRIEF
    # ============================================
    with tab4:
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
            sector_colors = [get_sector_color(k, st.session_state.sector_color_map) for k in metrics.sector_exposures.keys()]

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
