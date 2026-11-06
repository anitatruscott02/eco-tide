"""
📊 Eco-Tide — Factor Analysis
Deep-dive into environmental factor correlations, seasonal patterns, and compound events.

Sections:
  • Correlation Heatmap (all factors vs water level)
  • Feature Importance (sorted absolute correlation)
  • Interactive Scatter Plots with OLS trendline
  • Seasonal Decomposition (monthly averages)
  • Compound Event Analysis (multi-factor timeline & factor breakdown)
  • Monthly & Annual Trends
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px

from utils.data_loader import load_dataset
from models.risk_engine import detect_compound_events
from config.settings import THEME
from utils.theme import init_theme, render_theme_switcher, inject_theme_css, get_plotly_layout

# ── Dynamic Theme & Sidebar Switcher ────────────────────────────────────────
init_theme()
inject_theme_css()

with st.sidebar:
    render_theme_switcher()

# ─── Shared chart layout factory ───────────────────────────────────────────
def get_chart_layout(**overrides) -> dict:
    """Return a Plotly layout dictionary dynamically adapted to the active theme."""
    return get_plotly_layout(**overrides)

# ─── Data Loading ───────────────────────────────────────────────────────────

@st.cache_data(ttl=3600)
def load_analysis_data():
    return load_dataset()

dataset = load_analysis_data()

# ─── Page Header ────────────────────────────────────────────────────────────
st.markdown("""
<div style="display:flex; align-items:center; gap:14px; margin-bottom:0.3rem;">
    <div style="font-family:'Inter',sans-serif; font-weight:900; font-size:2rem;
                background: linear-gradient(135deg, #FF6B35, #FFD600);
                -webkit-background-clip:text; -webkit-text-fill-color:transparent;">
        📊 Factor Analysis
    </div>
</div>
<div style="font-family:'Inter',sans-serif; font-size:0.9rem; color:var(--text-secondary); font-weight:500; margin-bottom:1.5rem;">
    Explore how environmental factors correlate with flood risk &nbsp;•&nbsp;
    {} records &nbsp;•&nbsp; {} → {}
</div>
""".format(
    f"{len(dataset):,}",
    dataset.index.min().strftime("%d %b %Y"),
    dataset.index.max().strftime("%d %b %Y"),
), unsafe_allow_html=True)


# ─── Select numeric analysis columns ───────────────────────────────────────
ANALYSIS_COLS = [
    c for c in dataset.columns
    if dataset[c].dtype in ("float64", "float32", "int64", "int32")
    and c not in ("hour", "day_of_year", "month", "is_wet_season")
]

TARGET = "water_level_m"
if TARGET not in ANALYSIS_COLS:
    st.error("water_level_m column not found in dataset.")
    st.stop()


# ╔═══════════════════════════════════════════════════════════════════════════╗
# ║  1. CORRELATION HEATMAP                                                  ║
# ╚═══════════════════════════════════════════════════════════════════════════╝

st.markdown("""
<div class="section-card">
    <div class="section-title">🔥 Correlation Matrix</div>
    <div class="section-subtitle">
        Pearson correlations between all environmental factors. 
        Blue = strong positive, Red = strong negative.
    </div>
</div>
""", unsafe_allow_html=True)

corr_matrix = dataset[ANALYSIS_COLS].corr()

label_map = {
    "water_level_m": "Water Level",
    "tidal_component_m": "Tidal Component",
    "met_surge_m": "Met. Surge",
    "pressure_surge_m": "Pressure Surge",
    "wind_surge_m": "Wind Surge",
    "rainfall_surge_m": "Rain Surge",
    "temp_celsius": "Temperature",
    "humidity_pct": "Humidity",
    "rainfall_mm": "Rainfall",
    "pressure_hpa": "Pressure",
    "wind_speed_ms": "Wind Speed",
    "wind_dir_deg": "Wind Dir (°)",
    "soil_moisture": "Soil Moisture",
    "cloud_cover_pct": "Cloud Cover",
    "moon_phase": "Moon Phase",
    "moon_illumination": "Moon Illum.",
    "spring_tide_factor": "Spring Tide",
    "river_discharge_est": "River Discharge",
    "base_flow": "Base Flow",
    "sst_celsius": "SST",
    "wave_height_m": "Wave Height",
    "wave_period_s": "Wave Period",
    "wave_dir_deg": "Wave Dir (°)",
    "wind_dir_sin": "Wind Dir (sin)",
    "wind_dir_cos": "Wind Dir (cos)",
    "rainfall_6h": "Rainfall (6h)",
    "rainfall_24h": "Rainfall (24h)",
    "pressure_change_3h": "ΔP (3h)",
    "wind_speed_max_6h": "Wind Max (6h)",
    "water_level_change_3h": "ΔWL (3h)",
    "compound_risk": "Compound Risk",
}

display_labels = [label_map.get(c, c) for c in corr_matrix.columns]

fig_heatmap = go.Figure(data=go.Heatmap(
    z=corr_matrix.values,
    x=display_labels,
    y=display_labels,
    colorscale="RdBu_r",
    zmid=0,
    zmin=-1, zmax=1,
    text=np.round(corr_matrix.values, 2),
    texttemplate="%{text}",
    textfont=dict(size=10, color="#FFFFFF"),
    hoverongaps=False,
    hovertemplate="%{x} vs %{y}<br>r = %{z:.3f}<extra></extra>",
    colorbar=dict(
        title=dict(text="r", font=dict(color="#F8FAFC", size=13)),
        tickfont=dict(color="#F8FAFC", size=11),
        bgcolor="rgba(0,0,0,0)",
        borderwidth=0,
    ),
))

fig_heatmap.update_layout(get_chart_layout(
    title=dict(text="Correlation Heatmap — All Factors", font=dict(size=17, color="#F8FAFC")),
    height=640,
    margin=dict(l=140, r=40, t=60, b=120),
))
fig_heatmap.update_xaxes(
    tickangle=-45,
    tickfont=dict(size=11, color="#F8FAFC", family="Inter, sans-serif"),
    gridcolor="rgba(255,255,255,0.08)",
)
fig_heatmap.update_yaxes(
    tickfont=dict(size=11, color="#F8FAFC", family="Inter, sans-serif"),
    gridcolor="rgba(255,255,255,0.08)",
    autorange="reversed",
    automargin=True,
)

st.plotly_chart(fig_heatmap, use_container_width=True, config={"displayModeBar": False})


# ╔═══════════════════════════════════════════════════════════════════════════╗
# ║  2. FEATURE IMPORTANCE                                                   ║
# ╚═══════════════════════════════════════════════════════════════════════════╝

st.markdown("""
<div class="section-card">
    <div class="section-title">📊 Feature Importance — Correlation with Water Level</div>
    <div class="section-subtitle">
        Factors ranked by absolute Pearson correlation with water_level_m.
    </div>
</div>
""", unsafe_allow_html=True)

target_corr = corr_matrix[TARGET].drop(TARGET).abs().sort_values(ascending=True)
target_corr_signed = corr_matrix[TARGET].drop(TARGET)

colors = [
    "#0A84FF" if target_corr_signed[c] >= 0 else "#FF6B35"
    for c in target_corr.index
]

labels_fi = [label_map.get(c, c) for c in target_corr.index]

fig_importance = go.Figure(go.Bar(
    y=labels_fi,
    x=target_corr.values,
    orientation="h",
    marker=dict(
        color=colors,
        line=dict(width=0),
        opacity=0.9,
    ),
    text=[f"{v:.3f}" for v in target_corr.values],
    textposition="outside",
    textfont=dict(size=11, color="#F8FAFC", family="Inter, sans-serif"),
    cliponaxis=False,
    hovertemplate="%{y}: |r| = %{x:.3f}<extra></extra>",
))

fig_importance.update_layout(get_chart_layout(
    title=dict(
        text="Absolute Pearson Correlation with Water Level",
        font=dict(size=17, color="#F8FAFC", family="Inter, sans-serif"),
    ),
    height=max(500, len(target_corr) * 34),
    margin=dict(l=160, r=80, t=60, b=60),
    annotations=[
        dict(
            text="<span style='color:#0A84FF;font-weight:bold;'>■</span> Positive &nbsp;&nbsp; "
                 "<span style='color:#FF6B35;font-weight:bold;'>■</span> Negative",
            xref="paper", yref="paper",
            x=1, y=1.04, showarrow=False,
            font=dict(size=12, color="#F8FAFC"),
        ),
    ],
))
fig_importance.update_xaxes(
    title=dict(text="| Pearson Correlation Coefficient (r) |", font=dict(size=13, color="#F8FAFC")),
    tickfont=dict(size=12, color="#F8FAFC", family="Inter, sans-serif"),
    range=[0, min(1.05, target_corr.max() * 1.22)],
    gridcolor="rgba(255,255,255,0.12)",
)
fig_importance.update_yaxes(
    tickfont=dict(size=12, color="#F8FAFC", family="Inter, sans-serif"),
    gridcolor="rgba(255,255,255,0.08)",
    automargin=True,
)

st.plotly_chart(fig_importance, use_container_width=True, config={"displayModeBar": False})


# ╔═══════════════════════════════════════════════════════════════════════════╗
# ║  3. SCATTER PLOTS                                                        ║
# ╚═══════════════════════════════════════════════════════════════════════════╝

st.markdown("""
<div class="section-card">
    <div class="section-title">🔍 Scatter Plot — Factor vs Water Level</div>
    <div class="section-subtitle">
        Select an environmental factor to explore its relationship with water level.
    </div>
</div>
""", unsafe_allow_html=True)

scatter_options = [c for c in ANALYSIS_COLS if c != TARGET]
scatter_display = {c: label_map.get(c, c) for c in scatter_options}

selected_col = st.selectbox(
    "Select Factor",
    options=scatter_options,
    format_func=lambda x: scatter_display[x],
    index=scatter_options.index("rainfall_mm") if "rainfall_mm" in scatter_options else 0,
    label_visibility="collapsed",
)

sample_size = min(5000, len(dataset))
sample = dataset[[TARGET, selected_col]].dropna().sample(n=sample_size, random_state=42)

fig_scatter = px.scatter(
    sample,
    x=selected_col,
    y=TARGET,
    trendline="ols",
    labels={
        selected_col: scatter_display[selected_col],
        TARGET: "Water Level (m)",
    },
    color_discrete_sequence=["#00C7BE"],
    opacity=0.4,
)

fig_scatter.update_traces(
    selector=dict(mode="lines"),
    line=dict(color="#FF6B35", width=2.5, dash="dash"),
    opacity=1.0,
)

fig_scatter.update_traces(
    selector=dict(mode="markers"),
    marker=dict(size=4, line=dict(width=0)),
)

r_val = target_corr_signed.get(selected_col, 0)

fig_scatter.update_layout(get_chart_layout(
    title=dict(
        text=f"{scatter_display[selected_col]} vs Water Level  (r = {r_val:.3f})",
        font=dict(size=16, color="#F8FAFC"),
    ),
    height=450,
    showlegend=False,
    margin=dict(l=70, r=40, t=60, b=60),
))

st.plotly_chart(fig_scatter, use_container_width=True, config={"displayModeBar": False})


# ╔═══════════════════════════════════════════════════════════════════════════╗
# ║  4. SEASONAL DECOMPOSITION                                              ║
# ╚═══════════════════════════════════════════════════════════════════════════╝

st.markdown("""
<div class="section-card">
    <div class="section-title">📅 Seasonal Decomposition — Monthly Averages</div>
    <div class="section-subtitle">
        Average environmental conditions by month revealing wet/dry season patterns.
    </div>
</div>
""", unsafe_allow_html=True)

seasonal_cols = {
    "rainfall_mm": ("Rainfall (mm/hr)", "#0A84FF"),
    "water_level_m": ("Water Level (m)", "#00C7BE"),
    "temp_celsius": ("Temperature (°C)", "#FF1744"),
}

available_seasonal = {k: v for k, v in seasonal_cols.items() if k in dataset.columns}

if available_seasonal:
    monthly_avg = dataset.groupby(dataset.index.month)[list(available_seasonal.keys())].mean()
    month_names = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
                   "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]

    tab_labels = [v[0].split("(")[0].strip() for v in available_seasonal.values()]
    tabs_seasonal = st.tabs(tab_labels)

    for tab, (col, (title, color)) in zip(tabs_seasonal, available_seasonal.items()):
        with tab:
            fig_month = go.Figure()

            fig_month.add_trace(go.Bar(
                x=month_names,
                y=monthly_avg[col].values,
                marker=dict(
                    color=color,
                    opacity=0.85,
                    line=dict(width=0),
                ),
                text=[f"{v:.2f}" for v in monthly_avg[col].values],
                textposition="outside",
                textfont=dict(size=11, color="#F8FAFC"),
                hovertemplate="%{x}: %{y:.3f}<extra></extra>",
            ))

            fig_month.add_vrect(
                x0=2.5, x1=9.5,
                fillcolor="rgba(10,132,255,0.1)",
                layer="below",
                line_width=0,
                annotation_text="Wet Season",
                annotation_position="top left",
                annotation_font=dict(size=11, color="#38BDF8"),
            )

            fig_month.update_layout(get_chart_layout(
                title=dict(text=f"Monthly Average {title}", font=dict(size=16, color="#F8FAFC")),
                height=400,
                showlegend=False,
                margin=dict(l=70, r=40, t=60, b=60),
            ))
            fig_month.update_xaxes(
                tickfont=dict(size=12, color="#F8FAFC"),
                gridcolor="rgba(255,255,255,0.08)",
            )
            fig_month.update_yaxes(
                tickfont=dict(size=12, color="#F8FAFC"),
                gridcolor="rgba(255,255,255,0.08)",
            )

            st.plotly_chart(fig_month, use_container_width=True, config={"displayModeBar": False})
else:
    st.info("Seasonal columns not available in dataset.")


# ╔═══════════════════════════════════════════════════════════════════════════╗
# ║  5. COMPOUND EVENT ANALYSIS                                             ║
# ╚═══════════════════════════════════════════════════════════════════════════╝

st.markdown("""
<div class="section-card">
    <div class="section-title">⚡ Compound Event Analysis</div>
    <div class="section-subtitle">
        Compound events occur when 3+ adverse factors align simultaneously:
        high water level, heavy rainfall, low pressure, strong winds, spring tide.
    </div>
</div>
""", unsafe_allow_html=True)

conditions = detect_compound_events(dataset)

total_compound_hours = int(conditions["is_compound"].sum())
total_hours = len(conditions)
pct_compound = (total_compound_hours / total_hours * 100) if total_hours > 0 else 0

compound_flag = conditions["is_compound"].astype(int)
episode_starts = compound_flag.diff().fillna(0)
episode_id = (episode_starts == 1).cumsum() * compound_flag
n_episodes = episode_id.max()

if n_episodes > 0:
    episode_durations = episode_id[episode_id > 0].groupby(episode_id[episode_id > 0]).count()
    avg_duration = episode_durations.mean()
    max_duration = episode_durations.max()
else:
    avg_duration = 0
    max_duration = 0

factor_cols = ["high_water", "heavy_rain", "low_pressure", "strong_wind", "spring_tide"]
available_factor_cols = [c for c in factor_cols if c in conditions.columns]
compound_rows = conditions[conditions["is_compound"] == 1]

if len(compound_rows) > 0 and available_factor_cols:
    factor_combo = compound_rows[available_factor_cols].sum().sort_values(ascending=False)
    most_common_factor = factor_combo.index[0] if len(factor_combo) > 0 else "N/A"
    factor_display_names = {
        "high_water": "🌊 High Water",
        "heavy_rain": "🌧️ Heavy Rain",
        "low_pressure": "🔻 Low Pressure",
        "strong_wind": "💨 Strong Wind",
        "spring_tide": "🌙 Spring Tide",
    }
    most_common_display = factor_display_names.get(most_common_factor, most_common_factor)
else:
    most_common_display = "N/A"
    factor_combo = pd.Series(dtype=float)

# Stat pills
st.markdown(f"""
<div style="display:flex; flex-wrap:wrap; margin-bottom:1.2rem;">
    <div class="stat-pill">
        <span class="stat-label">Total Events</span>
        <span class="stat-val" style="color:var(--danger);">{n_episodes}</span>
    </div>
    <div class="stat-pill">
        <span class="stat-label">Compound Hours</span>
        <span class="stat-val" style="color:var(--warning);">{total_compound_hours:,}</span>
        <span class="stat-label">({pct_compound:.1f}%)</span>
    </div>
    <div class="stat-pill">
        <span class="stat-label">Avg Duration</span>
        <span class="stat-val" style="color:var(--primary);">{avg_duration:.1f}h</span>
    </div>
    <div class="stat-pill">
        <span class="stat-label">Max Duration</span>
        <span class="stat-val" style="color:var(--accent-orange);">{max_duration}h</span>
    </div>
    <div class="stat-pill">
        <span class="stat-label">Top Factor</span>
        <span class="stat-val">{most_common_display}</span>
    </div>
</div>
""", unsafe_allow_html=True)

# Spacing: Balanced 1:1 columns so horizontal bars have full legibility
comp_col1, comp_col2 = st.columns([1, 1], gap="medium")

with comp_col1:
    fig_timeline = go.Figure()

    fig_timeline.add_trace(go.Scatter(
        x=conditions.index,
        y=conditions["n_factors"],
        mode="lines",
        name="Active Factors",
        line=dict(color="#0A84FF", width=1),
        fill="tozeroy",
        fillcolor="rgba(10, 132, 255, 0.08)",
        hovertemplate="Factors active: %{y}<extra></extra>",
    ))

    compound_mask = conditions["is_compound"] == 1
    if compound_mask.any():
        fig_timeline.add_trace(go.Scatter(
            x=conditions.index[compound_mask],
            y=conditions["n_factors"][compound_mask],
            mode="markers",
            name="Compound Event",
            marker=dict(color="#FF1744", size=4, symbol="diamond", opacity=0.7),
            hovertemplate="⚡ COMPOUND — %{y} factors<extra></extra>",
        ))

    fig_timeline.add_hline(
        y=3, line=dict(color="#FFD600", width=1.5, dash="dash"),
        annotation_text="Compound Threshold (≥3)",
        annotation_position="right",
        annotation_font=dict(size=10, color="#FFD600"),
    )

    fig_timeline.update_layout(get_chart_layout(
        title=dict(text="Compound Event Timeline", font=dict(size=15, color="#F8FAFC")),
        height=380,
        xaxis_title="",
        yaxis_title="Active Adverse Factors",
        margin=dict(l=60, r=40, t=60, b=60),
    ))
    fig_timeline.update_xaxes(tickfont=dict(size=12, color="#F8FAFC"), gridcolor="rgba(255,255,255,0.1)")
    fig_timeline.update_yaxes(dtick=1, range=[0, 5.5], tickfont=dict(size=12, color="#F8FAFC"), gridcolor="rgba(255,255,255,0.1)")

    st.plotly_chart(fig_timeline, use_container_width=True, config={"displayModeBar": False})

with comp_col2:
    if len(factor_combo) > 0:
        factor_labels = [factor_display_names.get(c, c) for c in factor_combo.index]
        factor_colors = ["#FF1744", "#0A84FF", "#A78BFA", "#FF6B35", "#FFD600"]

        max_val = factor_combo.max() if len(factor_combo) > 0 else 100

        fig_factors = go.Figure(go.Bar(
            y=factor_labels,
            x=factor_combo.values,
            orientation="h",
            marker=dict(
                color=factor_colors[:len(factor_combo)],
                opacity=0.85,
                line=dict(width=0),
            ),
            text=[f"{int(v):,} h" for v in factor_combo.values],
            textposition="outside",
            textfont=dict(size=11, color="#F8FAFC", family="Inter, sans-serif"),
            cliponaxis=False,
            hovertemplate="%{y}: %{x:,} hours<extra></extra>",
        ))

        fig_factors.update_layout(get_chart_layout(
            title=dict(
                text="Factor Frequency<br><span style='font-size:10px;color:#94A3B8;'>"
                     "Hours active during compound events</span>",
                font=dict(size=14, color="#F8FAFC"),
            ),
            height=380,
            showlegend=False,
            margin=dict(l=140, r=70, t=60, b=60),
        ))
        fig_factors.update_xaxes(
            title=dict(text="Hours", font=dict(color="#F8FAFC")),
            tickfont=dict(size=12, color="#F8FAFC"),
            range=[0, max_val * 1.3],
            gridcolor="rgba(255,255,255,0.1)"
        )
        fig_factors.update_yaxes(
            tickfont=dict(size=12, color="#F8FAFC", family="Inter, sans-serif"),
            automargin=True,
            gridcolor="rgba(255,255,255,0.1)"
        )

        st.plotly_chart(fig_factors, use_container_width=True, config={"displayModeBar": False})
    else:
        st.info("No compound events detected in the dataset.")


# ╔═══════════════════════════════════════════════════════════════════════════╗
# ║  6. MONTHLY & SEASONAL TREND ANALYSIS                                    ║
# ╚═══════════════════════════════════════════════════════════════════════════╝

st.markdown("""
<div class="section-card">
    <div class="section-title">📅 Monthly & Seasonal Trend Analysis</div>
    <div class="section-subtitle">
        Average water levels by month across all years — identifies the most dangerous months for Lagos.
    </div>
</div>
""", unsafe_allow_html=True)

if "water_level_m" in dataset.columns and "month" in dataset.columns:
    monthly_avg = dataset.groupby("month")["water_level_m"].agg(["mean", "std", "max"]).reset_index()
    month_names = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
    monthly_avg["month_name"] = [month_names[int(m)-1] for m in monthly_avg["month"]]
    
    wet_months = [4, 5, 6, 7, 8, 9, 10, 11]
    colors_monthly = ["#0A84FF" if m in wet_months else "#FF6B35" for m in monthly_avg["month"]]
    
    fig_monthly = go.Figure()
    fig_monthly.add_trace(go.Bar(
        x=monthly_avg["month_name"], y=monthly_avg["mean"],
        marker_color=colors_monthly, opacity=0.85,
        text=[f"{v:.3f}" for v in monthly_avg["mean"]],
        textposition="outside", textfont=dict(size=11, color="#F8FAFC"),
        hovertemplate="<b>%{x}</b><br>Avg Water Level: %{y:.3f}m<extra></extra>",
        name="Avg Water Level"
    ))
    fig_monthly.add_trace(go.Scatter(
        x=monthly_avg["month_name"], y=monthly_avg["max"],
        mode="markers+lines", marker=dict(color="#FF1744", size=8),
        line=dict(color="#FF1744", width=1, dash="dot"),
        name="Peak Recorded", hovertemplate="<b>%{x}</b><br>Peak: %{y:.3f}m<extra></extra>"
    ))
    
    fig_monthly.update_layout(get_chart_layout(
        title=dict(text="Average vs Peak Water Level by Month", font=dict(size=16, color="#F8FAFC")),
        height=400,
        margin=dict(l=70, r=40, t=60, b=60),
        annotations=[
            dict(text="<span style='color:#0A84FF'>■</span> Wet Season &nbsp; <span style='color:#FF6B35'>■</span> Dry Season &nbsp; <span style='color:#FF1744'>●</span> Peak Recorded",
                 xref="paper", yref="paper", x=1, y=1.08, showarrow=False,
                 font=dict(size=11, color="#94A3B8")),
        ],
    ))
    fig_monthly.update_xaxes(tickfont=dict(size=12, color="#F8FAFC"), gridcolor="rgba(255,255,255,0.1)")
    fig_monthly.update_yaxes(title=dict(text="Water Level (m)", font=dict(color="#F8FAFC")), tickfont=dict(size=12, color="#F8FAFC"), gridcolor="rgba(255,255,255,0.1)")
    st.plotly_chart(fig_monthly, use_container_width=True, config={"displayModeBar": False})
    
    # Year-over-Year comparison
    st.markdown("""
    <div class="section-card">
        <div class="section-title">📈 Year-over-Year Comparison</div>
        <div class="section-subtitle">
            Is flooding getting worse due to climate change? Compare annual averages across all years.
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    dataset_copy = dataset.copy()
    dataset_copy["year"] = dataset_copy.index.year
    yearly_stats = dataset_copy.groupby("year")["water_level_m"].agg(["mean", "max", "count"]).reset_index()
    yearly_stats = yearly_stats[yearly_stats["count"] > 1000]
    
    fig_yearly = go.Figure()
    fig_yearly.add_trace(go.Bar(
        x=yearly_stats["year"].astype(str), y=yearly_stats["mean"],
        marker_color="#0A84FF", opacity=0.8, name="Annual Avg",
        text=[f"{v:.3f}" for v in yearly_stats["mean"]],
        textposition="outside", textfont=dict(size=11, color="#F8FAFC"),
    ))
    fig_yearly.add_trace(go.Scatter(
        x=yearly_stats["year"].astype(str), y=yearly_stats["max"],
        mode="markers+lines", marker=dict(color="#FF1744", size=10, symbol="diamond"),
        line=dict(color="#FF1744", width=2), name="Annual Peak",
    ))
    
    fig_yearly.update_layout(get_chart_layout(
        title=dict(text="Annual Water Level Trends — Climate Change Signal", font=dict(size=16, color="#F8FAFC")),
        height=400,
        margin=dict(l=70, r=40, t=60, b=60),
    ))
    fig_yearly.update_xaxes(title=dict(text="Year", font=dict(color="#F8FAFC")), tickfont=dict(size=12, color="#F8FAFC"), gridcolor="rgba(255,255,255,0.1)")
    fig_yearly.update_yaxes(title=dict(text="Water Level (m)", font=dict(color="#F8FAFC")), tickfont=dict(size=12, color="#F8FAFC"), gridcolor="rgba(255,255,255,0.1)")
    st.plotly_chart(fig_yearly, use_container_width=True, config={"displayModeBar": False})


# ─── Footer ─────────────────────────────────────────────────────────────────
st.markdown("""
<div style="text-align:center; padding:2rem 0 1rem; font-family:'Inter',sans-serif;
            font-size:0.75rem; color:#64748B;">
    Eco-Tide v1.0 &nbsp;•&nbsp; Factor Analysis &nbsp;•&nbsp; Lagos, Nigeria<br>
    All correlations are Pearson r computed on the full historical dataset.
</div>
""", unsafe_allow_html=True)
