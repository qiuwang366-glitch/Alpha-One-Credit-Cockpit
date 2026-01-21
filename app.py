"""
Alpha-One Credit Cockpit - Streamlit Dashboard

A Fixed Income Portfolio Analysis Application for Portfolio Managers.

Features:
- Rich/Cheap bond identification via stratified regression
- Net Carry efficiency analysis
- Valuation lag risk monitoring
- Executive summary generation
"""

import io
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from src.module_b.data_loader import DataLoader, DataValidationError
from src.module_b.analytics import PortfolioAnalyzer
from src.utils.constants import SECTOR_COLORS, Z_SCORE_THRESHOLDS

# Page configuration
st.set_page_config(
    page_title="Alpha-One Credit Cockpit",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom CSS for professional styling
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: 700;
        color: #1f2937;
        margin-bottom: 0.5rem;
    }
    .sub-header {
        font-size: 1rem;
        color: #6b7280;
        margin-bottom: 2rem;
    }
    .metric-card {
        background-color: #f9fafb;
        border-radius: 0.5rem;
        padding: 1rem;
        border-left: 4px solid #3b82f6;
    }
    .warning-card {
        border-left-color: #f59e0b;
    }
    .danger-card {
        border-left-color: #ef4444;
    }
    .stDataFrame {
        font-size: 0.875rem;
    }
</style>
""", unsafe_allow_html=True)


def format_currency(value: float) -> str:
    """Format value as currency."""
    if value >= 1e9:
        return f"${value/1e9:.2f}B"
    elif value >= 1e6:
        return f"${value/1e6:.2f}M"
    elif value >= 1e3:
        return f"${value/1e3:.1f}K"
    else:
        return f"${value:,.0f}"


def format_percentage(value: float) -> str:
    """Format value as percentage."""
    return f"{value * 100:.2f}%"


def apply_z_score_color(val):
    """Apply color styling based on Z-score."""
    if pd.isna(val):
        return ""
    if val < Z_SCORE_THRESHOLDS["rich"]:
        return "background-color: #fee2e2; color: #991b1b;"  # Red - Rich
    elif val > Z_SCORE_THRESHOLDS["cheap"]:
        return "background-color: #dcfce7; color: #166534;"  # Green - Cheap
    return ""


def apply_carry_color(val):
    """Apply color styling based on Net Carry."""
    if pd.isna(val):
        return ""
    if val < 0:
        return "background-color: #fee2e2; color: #991b1b;"  # Red - Bleeding
    elif val > 0.01:  # > 1%
        return "background-color: #dcfce7; color: #166534;"  # Green - Good carry
    return ""


def main():
    """Main application."""
    # Header
    st.markdown('<p class="main-header">📊 Alpha-One Credit Cockpit</p>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">Fixed Income Portfolio Optimization | Module B: Quantitative Scanner</p>', unsafe_allow_html=True)

    # Initialize session state
    if "data_loaded" not in st.session_state:
        st.session_state.data_loaded = False
    if "df" not in st.session_state:
        st.session_state.df = None
    if "analyzer" not in st.session_state:
        st.session_state.analyzer = None

    # ============================================
    # SIDEBAR
    # ============================================
    with st.sidebar:
        st.header("⚙️ Configuration")

        # Data Upload
        st.subheader("📁 Data Source")
        uploaded_file = st.file_uploader(
            "Upload Portfolio CSV",
            type=["csv"],
            help="Upload your portfolio export file (supports bilingual columns)",
        )

        use_sample = st.checkbox("Use Sample Data", value=not uploaded_file)

        if uploaded_file or use_sample:
            try:
                loader = DataLoader()

                if uploaded_file:
                    df = loader.load_from_upload(uploaded_file)
                else:
                    # Load sample data
                    sample_path = Path(__file__).parent / "data" / "portfolio.csv"
                    if sample_path.exists():
                        df = loader.load(sample_path)
                    else:
                        st.error("Sample data not found. Please upload a CSV file.")
                        return

                # Fit curves
                analyzer = PortfolioAnalyzer(df)
                analyzer.fit_sector_curves()

                st.session_state.df = df
                st.session_state.analyzer = analyzer
                st.session_state.data_loaded = True
                st.session_state.quality_report = loader.get_quality_report()

                st.success(f"✅ Loaded {len(df):,} bonds")

            except DataValidationError as e:
                st.error(f"Data validation error: {e}")
                return
            except Exception as e:
                st.error(f"Error loading data: {e}")
                return

        if not st.session_state.data_loaded:
            st.info("👆 Upload a CSV file or use sample data to begin")
            return

        st.divider()

        # Global Filters
        st.subheader("🔍 Filters")

        exclude_htm = st.checkbox(
            "Exclude HTM Assets",
            value=True,
            help="HTM (Hold-to-Maturity) bonds cannot be sold due to regulations",
        )

        available_sectors = sorted(st.session_state.df["Sector_L1"].unique())
        selected_sectors = st.multiselect(
            "Sectors",
            options=available_sectors,
            default=available_sectors,
            help="Select sectors to include in analysis",
        )

        min_liquidity = st.slider(
            "Min Liquidity Score",
            min_value=1,
            max_value=5,
            value=1,
            help="Filter by liquidity proxy (5 = High, 3 = Low)",
        )

        st.divider()

        # Data Quality Report
        if st.session_state.quality_report:
            with st.expander("📋 Data Quality Report"):
                report = st.session_state.quality_report.to_dict()
                for key, value in report.items():
                    st.metric(key, value)

    # ============================================
    # MAIN CONTENT - TABS
    # ============================================
    analyzer = st.session_state.analyzer
    df_filtered = analyzer.get_filtered_data(
        exclude_htm=exclude_htm,
        sectors=selected_sectors if selected_sectors else None,
        min_liquidity=min_liquidity,
    )

    # Re-fit curves on filtered data if significantly different
    filtered_analyzer = PortfolioAnalyzer(df_filtered)
    filtered_analyzer.fit_sector_curves()

    tab1, tab2, tab3 = st.tabs([
        "📈 The Matrix",
        "🔬 Optimization Lab",
        "📋 Management Brief",
    ])

    # ============================================
    # TAB 1: The Matrix (Scatter Plot)
    # ============================================
    with tab1:
        st.header("Duration-Yield Matrix with Sector Curves")

        col1, col2, col3 = st.columns([2, 1, 1])
        with col1:
            st.markdown(f"**Showing {len(df_filtered):,} bonds** | "
                       f"Total Exposure: {format_currency(df_filtered['Nominal_USD'].sum())}")

        # Build scatter plot
        fig = go.Figure()

        # Add scatter points for each sector
        for sector in selected_sectors:
            sector_data = df_filtered[df_filtered["Sector_L1"] == sector]
            if len(sector_data) == 0:
                continue

            color = SECTOR_COLORS.get(sector, "#999999")

            # Create hover text
            hover_text = sector_data.apply(
                lambda row: (
                    f"<b>{row['Ticker']}</b><br>"
                    f"Name: {row.get('Name', 'N/A')}<br>"
                    f"Duration: {row['Duration']:.2f}<br>"
                    f"Yield: {row['Yield']*100:.2f}%<br>"
                    f"Net Carry: {row['Net_Carry']*100:.2f}%<br>"
                    f"Z-Score: {row['Z_Score']:.2f}<br>"
                    f"Nominal: {format_currency(row['Nominal_USD'])}"
                ),
                axis=1,
            )

            fig.add_trace(go.Scatter(
                x=sector_data["Duration"],
                y=sector_data["Yield"] * 100,  # Convert to percentage
                mode="markers",
                name=sector,
                marker=dict(
                    size=8,
                    color=color,
                    opacity=0.7,
                    line=dict(width=1, color="white"),
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
                        y=y_curve * 100,  # Convert to percentage
                        mode="lines",
                        name=f"{sector} Curve",
                        line=dict(color=color, width=2, dash="dash"),
                        showlegend=False,
                        hoverinfo="skip",
                    ))
                except Exception:
                    pass

        fig.update_layout(
            xaxis_title="Duration (Years)",
            yaxis_title="Yield (%)",
            legend_title="Sector",
            hovermode="closest",
            height=600,
            template="plotly_white",
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1,
            ),
        )

        st.plotly_chart(fig, use_container_width=True)

        # Regression Statistics
        with st.expander("📊 Regression Statistics by Sector"):
            regression_results = filtered_analyzer.get_regression_results()
            if regression_results:
                stats_data = [r.to_dict() for r in regression_results.values()]
                stats_df = pd.DataFrame(stats_data)
                st.dataframe(stats_df, use_container_width=True, hide_index=True)
            else:
                st.info("Not enough data to fit curves")

    # ============================================
    # TAB 2: Optimization Lab
    # ============================================
    with tab2:
        st.header("Actionable Alpha Identification")

        col1, col2 = st.columns(2)

        with col1:
            st.subheader("🔴 Sell Candidates (Rich & Low Carry)")
            st.markdown("*Bonds with Z-Score < -1.5 that are expensive relative to their sector curve*")

            sell_candidates = filtered_analyzer.get_sell_candidates(
                z_threshold=-1.5,
                exclude_htm=exclude_htm,
            )

            if len(sell_candidates) > 0:
                display_cols = ["Ticker", "Name", "Sector_L1", "Duration", "Yield", "Net_Carry", "Z_Score", "Nominal_USD"]
                display_cols = [c for c in display_cols if c in sell_candidates.columns]

                styled_df = sell_candidates[display_cols].copy()
                styled_df["Yield"] = styled_df["Yield"].apply(format_percentage)
                styled_df["Net_Carry"] = styled_df["Net_Carry"].apply(format_percentage)
                styled_df["Nominal_USD"] = styled_df["Nominal_USD"].apply(format_currency)
                styled_df["Z_Score"] = styled_df["Z_Score"].round(2)

                st.dataframe(
                    styled_df,
                    use_container_width=True,
                    hide_index=True,
                    column_config={
                        "Z_Score": st.column_config.NumberColumn(
                            "Z-Score",
                            help="Negative = Rich/Expensive",
                            format="%.2f",
                        ),
                    },
                )

                total_exposure = sell_candidates["Nominal_USD"].sum()
                st.metric(
                    "Total Sell Candidate Exposure",
                    format_currency(total_exposure),
                    delta=f"{len(sell_candidates)} bonds",
                )
            else:
                st.success("✅ No rich bonds identified with current filters")

        with col2:
            st.subheader("💸 Bleeding Assets (Negative Carry)")
            st.markdown("*Bonds where Yield < FTP (costing more to fund than they return)*")

            bleeding_assets = filtered_analyzer.get_bleeding_assets(exclude_htm=exclude_htm)

            if len(bleeding_assets) > 0:
                display_cols = ["Ticker", "Name", "Sector_L1", "Duration", "Yield", "FTP", "Net_Carry", "Nominal_USD"]
                display_cols = [c for c in display_cols if c in bleeding_assets.columns]

                styled_df = bleeding_assets[display_cols].copy()
                styled_df["Yield"] = styled_df["Yield"].apply(format_percentage)
                styled_df["FTP"] = styled_df["FTP"].apply(format_percentage)
                styled_df["Net_Carry"] = styled_df["Net_Carry"].apply(format_percentage)
                styled_df["Nominal_USD"] = styled_df["Nominal_USD"].apply(format_currency)

                st.dataframe(styled_df, use_container_width=True, hide_index=True)

                total_bleed = bleeding_assets["Nominal_USD"].sum()
                annual_drag = (bleeding_assets["Net_Carry"] * bleeding_assets["Nominal_USD"]).sum()
                st.metric(
                    "Bleeding Exposure",
                    format_currency(total_bleed),
                    delta=f"Annual Drag: {format_currency(abs(annual_drag))}",
                    delta_color="inverse",
                )
            else:
                st.success("✅ No negative carry bonds identified")

        st.divider()

        # Carry Efficiency Analysis
        st.subheader("📊 Carry Efficiency Distribution")

        fig_carry = px.histogram(
            df_filtered,
            x="Carry_Efficiency",
            nbins=50,
            color="Sector_L1",
            color_discrete_map=SECTOR_COLORS,
            title="Carry Efficiency (Net Carry / Duration)",
            labels={"Carry_Efficiency": "Carry Efficiency", "count": "Count"},
        )
        fig_carry.add_vline(x=0, line_dash="dash", line_color="red", annotation_text="Zero Efficiency")
        fig_carry.update_layout(height=400, template="plotly_white")

        st.plotly_chart(fig_carry, use_container_width=True)

    # ============================================
    # TAB 3: Management Brief
    # ============================================
    with tab3:
        st.header("Executive Summary Generator")

        if st.button("📄 Generate Executive Summary", type="primary"):
            with st.spinner("Generating summary..."):
                summary = filtered_analyzer.generate_executive_summary()
                st.markdown(summary)

                # Download button
                st.download_button(
                    label="📥 Download Summary (Markdown)",
                    data=summary,
                    file_name="portfolio_summary.md",
                    mime="text/markdown",
                )

        st.divider()

        # Key Metrics Overview
        st.subheader("📈 Portfolio Metrics")

        metrics = filtered_analyzer.calculate_portfolio_metrics()

        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric(
                "Total AUM",
                format_currency(metrics.total_aum),
                help="Total Assets Under Management",
            )
            st.metric(
                "Holdings",
                f"{filtered_analyzer.df.shape[0]:,}",
            )

        with col2:
            st.metric(
                "Weighted Duration",
                f"{metrics.weighted_duration:.2f} yrs",
                help="Market-value weighted average duration",
            )
            st.metric(
                "Weighted Yield",
                format_percentage(metrics.weighted_yield),
            )

        with col3:
            st.metric(
                "Net Carry (Wtd)",
                format_percentage(metrics.weighted_net_carry),
                delta="Positive" if metrics.weighted_net_carry > 0 else "Negative",
                delta_color="normal" if metrics.weighted_net_carry > 0 else "inverse",
            )
            st.metric(
                "Negative Carry Count",
                metrics.negative_carry_count,
                delta=format_currency(metrics.negative_carry_exposure),
                delta_color="inverse",
            )

        with col4:
            st.metric(
                "Tradeable Holdings",
                metrics.tradeable_count,
                help="Bonds that can be sold (non-HTM)",
            )
            st.metric(
                "HTM Locked",
                metrics.htim_count,
                delta=format_currency(metrics.htm_exposure),
            )

        # Sector Allocation Chart
        st.subheader("🥧 Sector Allocation")

        fig_sector = px.pie(
            values=list(metrics.sector_exposures.values()),
            names=list(metrics.sector_exposures.keys()),
            color=list(metrics.sector_exposures.keys()),
            color_discrete_map=SECTOR_COLORS,
            hole=0.4,
        )
        fig_sector.update_layout(height=400)

        st.plotly_chart(fig_sector, use_container_width=True)

        # Full Data Export
        st.subheader("📥 Data Export")

        col1, col2 = st.columns(2)

        with col1:
            csv_buffer = io.StringIO()
            df_filtered.to_csv(csv_buffer, index=False)
            st.download_button(
                label="Download Filtered Data (CSV)",
                data=csv_buffer.getvalue(),
                file_name="portfolio_filtered.csv",
                mime="text/csv",
            )

        with col2:
            # Regression results export
            regression_results = filtered_analyzer.get_regression_results()
            if regression_results:
                reg_data = [r.to_dict() for r in regression_results.values()]
                reg_df = pd.DataFrame(reg_data)
                reg_csv = io.StringIO()
                reg_df.to_csv(reg_csv, index=False)
                st.download_button(
                    label="Download Regression Stats (CSV)",
                    data=reg_csv.getvalue(),
                    file_name="regression_stats.csv",
                    mime="text/csv",
                )


if __name__ == "__main__":
    main()
