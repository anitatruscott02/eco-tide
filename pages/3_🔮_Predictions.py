"""
Eco-Tide: 🔮 48-Hour Flood Predictions
Forecast water levels with confidence bands, risk timeline, and climate stress test analysis.
"""

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from utils.data_loader import load_dataset, get_latest_data, load_live_forecast
from models.risk_engine import classify_risk_level, compute_zone_risks
from models.tidal_analysis import harmonic_predict
from components.traffic_light import render_traffic_light
from config.settings import LAGOS_ZONES, THEME, ABSOLUTE_SURGE_THRESHOLDS
from utils.theme import init_theme, render_theme_switcher, inject_theme_css

# ── Dynamic Theme & Sidebar Switcher ────────────────────────────────────────
init_theme()
inject_theme_css()

with st.sidebar:
    render_theme_switcher()

st.markdown("""
<style>
/* Slider styling */
div[data-testid="stSlider"] label {
    color: var(--text-primary) !important;
    font-family: 'Inter', sans-serif !important;
}

/* Info / warning boxes */
.info-box {
    background: rgba(10, 132, 255, 0.08);
    border: 1px solid rgba(10, 132, 255, 0.25);
    border-radius: 12px;
    padding: 16px 20px;
    color: var(--primary, #0A84FF);
    font-size: 0.9rem;
    margin-bottom: 16px;
}
.warning-box {
    background: rgba(255, 214, 0, 0.08);
    border: 1px solid rgba(255, 214, 0, 0.25);
    border-radius: 12px;
    padding: 16px 20px;
    color: var(--warning, #E6A800);
    font-size: 0.9rem;
    margin-bottom: 16px;
}

/* Risk zone card */
.risk-zone-card {
    background: var(--bg-card);
    border-radius: 12px;
    padding: 12px 16px;
    border: 1px solid var(--border-card);
    margin-bottom: 8px;
}
</style>
""", unsafe_allow_html=True)

from components.charts import _theme_colors
tc = _theme_colors()

# ─── Header ─────────────────────────────────────────────────────────────────
st.markdown("""
<div class="page-header">
    <h1>🔮 48-Hour Flood Predictions</h1>
    <p style="color:var(--text-secondary);">Forecast water levels with confidence bands and risk assessment</p>
</div>
""", unsafe_allow_html=True)

# ─── Load Data ──────────────────────────────────────────────────────────────
try:
    dataset = load_dataset()
except Exception:
    st.error("⚠️ Dataset not found. Please run the data pipeline first (`data/fetch_real_data.py`).")
    st.stop()

# Check if model is available
model_data = None
try:
    from utils.data_loader import load_model
    model_data = load_model()
except Exception:
    pass

has_model = model_data is not None

# ─── Generate forecast data ────────────────────────────────────────────────
# 48-hour forward projection window
FORECAST_HOURS = 48
HISTORY_HOURS = 72

recent = dataset.tail(HISTORY_HOURS + FORECAST_HOURS)
history = recent.iloc[:HISTORY_HOURS]
future = recent.iloc[HISTORY_HOURS:]

# Generate tidal prediction for the "future" window
future_dates = future.index
tidal_future = harmonic_predict(future_dates)

if has_model and "results" in model_data:
    st.markdown('<div class="info-box">✅ <strong>SARIMAX model loaded.</strong> Forecast uses trained model predictions.</div>', unsafe_allow_html=True)

    # Use model forecast
    try:
        model_results = model_data["results"]
        features = model_data.get("features", [])
        scaler = model_data.get("scaler", None)

        available = [f for f in features if f in future.columns]
        if available and scaler is not None:
            exog_future = pd.DataFrame(
                scaler.transform(future[available]),
                columns=available,
                index=future.index
            )
            forecast_result = model_results.get_forecast(
                steps=len(future), exog=exog_future
            )
            surge_pred = forecast_result.predicted_mean
            conf = forecast_result.conf_int()
            forecast_wl = tidal_future.values + surge_pred.values
            lower_ci = tidal_future.values + conf.iloc[:, 0].values
            upper_ci = tidal_future.values + conf.iloc[:, 1].values
        else:
            raise ValueError("Features mismatch")
    except Exception:
        # Fallback to persistence
        forecast_wl = future["water_level_m"].values if "water_level_m" in future.columns else tidal_future.values
        std = history["water_level_m"].std() if "water_level_m" in history.columns else 0.1
        lower_ci = forecast_wl - 1.96 * std
        upper_ci = forecast_wl + 1.96 * std
else:
    st.markdown(
        '<div class="warning-box">⚠️ <strong>No trained model found.</strong> '
        'Using persistence forecast (last observed value repeated). '
        'Train the model on the <strong>🎓 Model Performance</strong> page for better predictions.</div>',
        unsafe_allow_html=True
    )

    # Persistence forecast: use last known water level
    if "water_level_m" in history.columns:
        last_wl = history["water_level_m"].iloc[-1]
        # Blend persistence with tidal signal for realism
        tidal_anomaly = tidal_future.values - tidal_future.values.mean()
        forecast_wl = last_wl + tidal_anomaly
    else:
        forecast_wl = tidal_future.values

    std = history["water_level_m"].std() if "water_level_m" in history.columns else 0.1
    # Widen confidence band with forecast horizon
    hours_ahead = np.arange(1, len(future) + 1)
    widening = std * np.sqrt(hours_ahead / FORECAST_HOURS)
    lower_ci = forecast_wl - 1.96 * widening
    upper_ci = forecast_wl + 1.96 * widening

# --- Live Forecast Integration ---
try:
    live_forecast = load_live_forecast()
    if live_forecast is not None and not live_forecast.empty:
        st.markdown('<div class="info-box">🌐 <strong>Using live Open-Meteo forecast data</strong></div>', unsafe_allow_html=True)
        min_len = min(len(live_forecast), len(future))
        live_future = live_forecast.head(min_len)
        
        future = future.copy()
        
        if "rainfall_mm" in live_future.columns:
            future.loc[future.index[:min_len], "rainfall_mm"] = live_future["rainfall_mm"].values
        if "wind_speed_ms" in live_future.columns:
            future.loc[future.index[:min_len], "wind_speed_ms"] = live_future["wind_speed_ms"].values
        if "pressure_hpa" in live_future.columns:
            future.loc[future.index[:min_len], "pressure_hpa"] = live_future["pressure_hpa"].values
            
        if "tidal_water_level_m" in live_future.columns:
            ibe_m = np.maximum(0, (1013.25 - live_future["pressure_hpa"].values) * 0.01)
            wind_setup_m = (live_future["wind_speed_ms"].values**2) / (9.81 * 10.0) * 0.01
            forecast_wl[:min_len] = live_future["tidal_water_level_m"].values + ibe_m + wind_setup_m
except Exception:
    pass


# ═══════════════════════════════════════════════════════════════════════════
#  SECTION 1: FORECAST CHART
# ═══════════════════════════════════════════════════════════════════════════
st.markdown("""
<div class="glass-card">
    <div class="section-title">📈 Water Level Forecast — Next 48 Hours</div>
    <div class="section-subtitle">Predicted water level with confidence band and risk thresholds</div>
</div>
""", unsafe_allow_html=True)

fig_forecast = go.Figure()

# Historical water level
if "water_level_m" in history.columns:
    fig_forecast.add_trace(go.Scatter(
        x=history.index,
        y=history["water_level_m"],
        name="Observed",
        mode="lines",
        line=dict(color="#0A84FF", width=2),
        hovertemplate="<b>Observed</b><br>%{x|%b %d %H:%M}<br>%{y:.3f} m<extra></extra>",
    ))

# Confidence band
fig_forecast.add_trace(go.Scatter(
    x=list(future_dates) + list(future_dates[::-1]),
    y=list(upper_ci) + list(lower_ci[::-1]),
    fill="toself",
    fillcolor="rgba(0, 199, 190, 0.12)",
    line=dict(color="rgba(0,0,0,0)"),
    name="95% Confidence",
    hoverinfo="skip",
))

# Forecast line
fig_forecast.add_trace(go.Scatter(
    x=future_dates,
    y=forecast_wl,
    name="Forecast",
    mode="lines",
    line=dict(color="#00C7BE", width=2.5, dash="dot"),
    hovertemplate="<b>Forecast</b><br>%{x|%b %d %H:%M}<br>%{y:.3f} m<extra></extra>",
))

# Risk threshold lines
thresholds = ABSOLUTE_SURGE_THRESHOLDS
all_dates = list(history.index) + list(future_dates)
x_range = [min(all_dates), max(all_dates)]

fig_forecast.add_hline(
    y=thresholds["green_max_m"],
    line=dict(color="#00C853", width=1, dash="dash"),
    annotation_text="Safe Limit",
    annotation=dict(font_color="#00C853", font_size=10),
)
fig_forecast.add_hline(
    y=thresholds["amber_max_m"],
    line=dict(color="#FFD600", width=1, dash="dash"),
    annotation_text="Caution",
    annotation=dict(font_color="#FFD600", font_size=10),
)
fig_forecast.add_hline(
    y=thresholds["red_min_m"],
    line=dict(color="#FF1744", width=1, dash="dash"),
    annotation_text="Danger",
    annotation=dict(font_color="#FF1744", font_size=10),
)

# Now/forecast boundary
if len(history) > 0:
    fig_forecast.add_vline(
        x=history.index[-1].timestamp() * 1000,
        line=dict(color="rgba(255,255,255,0.3)", width=1, dash="dot"),
        annotation_text="Now →",
        annotation=dict(font_color="#8B95B2", font_size=11),
    )

fig_forecast.update_layout(
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor=tc["plot_bg"],
    font=dict(family="Inter, sans-serif", color=tc["text"]),
    height=420,
    margin=dict(l=50, r=30, t=30, b=50),
    legend=dict(
        orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1,
        font=dict(size=11, color=tc["text_secondary"]),
    ),
    xaxis=dict(
        gridcolor=tc["grid"],
        title="Time",
        title_font=dict(size=12),
    ),
    yaxis=dict(
        gridcolor=tc["grid"],
        title="Water Level (m)",
        title_font=dict(size=12),
    ),
    hovermode="x unified",
)
st.plotly_chart(fig_forecast, use_container_width=True)


# ═══════════════════════════════════════════════════════════════════════════
#  SECTION 2: RISK TIMELINE
# ═══════════════════════════════════════════════════════════════════════════
st.markdown("""
<div class="glass-card">
    <div class="section-title">🕐 Risk Timeline — Hour-by-Hour</div>
    <div class="section-subtitle">Projected risk level for each forecast hour</div>
</div>
""", unsafe_allow_html=True)

# Compute risk per forecast hour
risk_colors_map = {"green": "#00C853", "amber": "#FFD600", "red": "#FF1744"}
risk_levels_hourly = []
risk_scores_hourly = []

for i in range(len(forecast_wl)):
    wl = forecast_wl[i]
    rain = future["rainfall_mm"].iloc[i] if "rainfall_mm" in future.columns else 0
    wind = future["wind_speed_ms"].iloc[i] if "wind_speed_ms" in future.columns else 0
    pres = future["pressure_hpa"].iloc[i] if "pressure_hpa" in future.columns else 1013
    risk = classify_risk_level(wl, rain, wind, pres, zone_elevation_m=3.0)
    risk_levels_hourly.append(risk["level"])
    risk_scores_hourly.append(risk["score"])

# Build timeline bar chart
timeline_colors = [risk_colors_map.get(lev, "#8B95B2") for lev in risk_levels_hourly]

fig_timeline = go.Figure()
fig_timeline.add_trace(go.Bar(
    x=future_dates,
    y=[1] * len(future_dates),
    marker_color=timeline_colors,
    marker_line=dict(width=0),
    hovertemplate=(
        "<b>%{x|%b %d %H:%M}</b><br>"
        "Risk: %{customdata[0]}<br>"
        "Score: %{customdata[1]:.2f}<extra></extra>"
    ),
    customdata=list(zip(
        [lev.upper() for lev in risk_levels_hourly],
        risk_scores_hourly,
    )),
))

# Find peak risk
peak_idx = int(np.argmax(risk_scores_hourly))
peak_time = future_dates[peak_idx]

fig_timeline.add_annotation(
    x=peak_time,
    y=1.15,
    text=f"⚠ Peak Risk",
    showarrow=True,
    arrowhead=2,
    arrowsize=1,
    arrowwidth=1.5,
    arrowcolor="#FF6B35",
    font=dict(color="#FF6B35", size=11, family="Inter"),
    bordercolor="#FF6B35",
    borderwidth=1,
    borderpad=4,
    bgcolor="rgba(19,24,55,0.9)",
)

fig_timeline.update_layout(
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor=tc["plot_bg"],
    font=dict(family="Inter, sans-serif", color=tc["text"]),
    height=130,
    margin=dict(l=50, r=30, t=30, b=30),
    showlegend=False,
    xaxis=dict(
        gridcolor=tc["grid"],
        tickformat="%H:%M\n%b %d",
    ),
    yaxis=dict(visible=False, range=[0, 1.4]),
    bargap=0.02,
)
st.plotly_chart(fig_timeline, use_container_width=True)

# Summary metrics
col1, col2, col3, col4 = st.columns(4)

n_red = sum(1 for l in risk_levels_hourly if l == "red")
n_amber = sum(1 for l in risk_levels_hourly if l == "amber")
n_green = sum(1 for l in risk_levels_hourly if l == "green")

with col1:
    st.markdown(f"""
    <div class="glass-card" style="text-align:center;">
        <div style="color:var(--danger);font-size:2rem;font-weight:800;">{n_red}</div>
        <div style="color:var(--text-secondary);font-size:0.8rem;font-weight:600;">DANGER HOURS</div>
    </div>
    """, unsafe_allow_html=True)
with col2:
    st.markdown(f"""
    <div class="glass-card" style="text-align:center;">
        <div style="color:var(--warning);font-size:2rem;font-weight:800;">{n_amber}</div>
        <div style="color:var(--text-secondary);font-size:0.8rem;font-weight:600;">CAUTION HOURS</div>
    </div>
    """, unsafe_allow_html=True)
with col3:
    st.markdown(f"""
    <div class="glass-card" style="text-align:center;">
        <div style="color:var(--success);font-size:2rem;font-weight:800;">{n_green}</div>
        <div style="color:var(--text-secondary);font-size:0.8rem;font-weight:600;">SAFE HOURS</div>
    </div>
    """, unsafe_allow_html=True)
with col4:
    st.markdown(f"""
    <div class="glass-card" style="text-align:center;">
        <div style="color:var(--accent-orange);font-size:1.2rem;font-weight:700;">{peak_time.strftime('%b %d, %H:%M')}</div>
        <div style="color:var(--text-secondary);font-size:0.8rem;font-weight:600;">PEAK RISK TIME</div>
    </div>
    """, unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════════════════
#  SECTION 3: CLIMATE STRESS TEST ANALYSIS
# ═══════════════════════════════════════════════════════════════════════════
st.markdown("""
<div class="glass-card">
    <div class="section-title">🎛️ Climate Stress Test & Hydraulic Sensitivity Analysis</div>
    <div class="section-subtitle">Evaluate infrastructure resilience and zone vulnerability across parameterized rainfall, tidal surge, and drainage conditions</div>
</div>
""", unsafe_allow_html=True)

sim_col1, sim_col2 = st.columns([1, 2])

with sim_col1:
    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    st.markdown("##### ⚙️ Environmental Conditions")

    sim_rainfall = st.slider(
        "🌧️ Rainfall (mm/hr)", 0, 100, 5, 1,
        help="Rainfall intensity in millimeters per hour"
    )
    sim_wind = st.slider(
        "💨 Wind Speed (m/s)", 0, 30, 5, 1,
        help="Surface wind speed in meters per second"
    )
    sim_pressure = st.slider(
        "🌀 Pressure (hPa)", 990, 1025, 1013, 1,
        help="Sea-level atmospheric pressure"
    )
    sim_moon = st.slider(
        "🌕 Spring Tide Factor", 0.0, 1.0, 0.5, 0.05,
        help="0 = Neap tide (minimal), 1 = Spring tide (maximum)"
    )
    sim_drainage_multiplier = st.slider(
        "🗑️ Drainage Efficiency", 0.0, 1.0, 1.0, 0.1,
        help="1.0 = Normal Capacity, 0.0 = Fully Blocked by Waste"
    )
    sim_soil = st.slider(
        '💧 Soil Saturation', 0.0, 1.0, 0.3, 0.05,
        help='0.0 = Completely Dry, 1.0 = Fully Saturated (e.g. after 3 days of heavy rain)'
    )

    # Compute water level from spring tide factor
    sim_water_level = 0.5 + sim_moon * 0.8  # MSL + tidal range scaled by moon phase

    # Pressure surge (inverse barometer: 1 hPa → ~1 cm)
    sim_water_level += max(0, 1013.25 - sim_pressure) * 0.01

    # Wind setup (simplified)
    sim_water_level += (sim_wind / 25.0) * 0.15

    st.markdown(f"""
    <div style="
        background: rgba(10, 132, 255, 0.08);
        border: 1px solid rgba(10, 132, 255, 0.2);
        border-radius: 10px; padding: 12px; margin-top: 12px;
        text-align: center;
    ">
        <div style="color: var(--text-secondary); font-size: 0.8rem; font-weight: 700;">EFFECTIVE WATER LEVEL</div>
        <div style="color: var(--primary); font-size: 1.8rem; font-weight: 800;">
            {sim_water_level:.2f} m
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Reference zone: Eti-Osa (elevation 2m)
    ref_risk = classify_risk_level(
        water_level_m=sim_water_level,
        rainfall_mm=sim_rainfall,
        wind_speed_ms=sim_wind,
        pressure_hpa=sim_pressure,
        zone_elevation_m=2.0,
        zone_drainage_capacity=0.4 * sim_drainage_multiplier,
        soil_moisture=sim_soil
    )

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown(
        '<div style="text-align:center;color:var(--text-secondary);font-size:0.8rem;margin-bottom:8px;">'
        'ETE-OSA RISK (Ref. Zone, 2m elev.)</div>',
        unsafe_allow_html=True,
    )
    # Center the traffic light
    tl_cols = st.columns([1, 1, 1])
    with tl_cols[1]:
        render_traffic_light(
            level=ref_risk["level"],
            label=ref_risk["label"],
            action=ref_risk["action"],
            score=ref_risk["score"],
        )

    st.markdown('</div>', unsafe_allow_html=True)

with sim_col2:
    # Compute risk for all 20 zones with these conditions
    zone_risks = compute_zone_risks(
        water_level_m=sim_water_level,
        rainfall_mm=sim_rainfall,
        wind_speed_ms=sim_wind,
        pressure_hpa=sim_pressure,
        drainage_multiplier=sim_drainage_multiplier,
        soil_moisture=sim_soil,
    )

    zone_names = [z["name"] for z in zone_risks]
    zone_scores = [z["score"] for z in zone_risks]
    zone_levels = [z["level"] for z in zone_risks]
    zone_elevations = [z["elevation_m"] for z in zone_risks]
    bar_colors = [risk_colors_map.get(lev, "#8B95B2") for lev in zone_levels]

    fig_zones = go.Figure()
    fig_zones.add_trace(go.Bar(
        x=zone_names,
        y=zone_scores,
        marker_color=bar_colors,
        marker_line=dict(width=0),
        text=[f"{s:.2f}" for s in zone_scores],
        textposition="outside",
        textfont=dict(size=9, color="#E0E0E0"),
        hovertemplate=(
            "<b>%{x}</b><br>"
            "Risk Score: %{y:.3f}<br>"
            "Elevation: %{customdata[0]:.0f}m<br>"
            "Level: %{customdata[1]}<extra></extra>"
        ),
        customdata=list(zip(zone_elevations, [l.upper() for l in zone_levels])),
    ))

    # Threshold lines
    fig_zones.add_hline(y=0.6, line=dict(color="#FF1744", width=1, dash="dash"),
                        annotation_text="Danger", annotation=dict(font_color="#FF1744", font_size=9))
    fig_zones.add_hline(y=0.3, line=dict(color="#FFD600", width=1, dash="dash"),
                        annotation_text="Caution", annotation=dict(font_color="#FFD600", font_size=9))

    fig_zones.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor=tc["plot_bg"],
        font=dict(family="Inter, sans-serif", color=tc["text"]),
        height=480,
        margin=dict(l=50, r=30, t=40, b=100),
        title=dict(
            text="Risk Score Across All 20 Lagos Zones",
            font=dict(size=14, color=tc["text"]),
        ),
        xaxis=dict(
            gridcolor=tc["grid"],
            tickangle=-45,
            tickfont=dict(size=10),
        ),
        yaxis=dict(
            gridcolor=tc["grid"],
            title="Risk Score",
            range=[0, max(max(zone_scores) + 0.15, 0.8)],
        ),
        showlegend=False,
    )
    st.plotly_chart(fig_zones, use_container_width=True)

    # Summary row
    n_sim_red = sum(1 for l in zone_levels if l == "red")
    n_sim_amber = sum(1 for l in zone_levels if l == "amber")
    n_sim_green = sum(1 for l in zone_levels if l == "green")

    st.markdown(f"""
    <div style="display:flex;gap:16px;justify-content:center;flex-wrap:wrap;">
        <div class="glass-card" style="text-align:center;flex:1;min-width:120px;">
            <div style="color:var(--danger);font-size:1.6rem;font-weight:800;">{n_sim_red}</div>
            <div style="color:var(--text-secondary);font-size:0.75rem;font-weight:600;">ZONES IN DANGER</div>
        </div>
        <div class="glass-card" style="text-align:center;flex:1;min-width:120px;">
            <div style="color:var(--warning);font-size:1.6rem;font-weight:800;">{n_sim_amber}</div>
            <div style="color:var(--text-secondary);font-size:0.75rem;font-weight:600;">ZONES CAUTIONED</div>
        </div>
        <div class="glass-card" style="text-align:center;flex:1;min-width:120px;">
            <div style="color:var(--success);font-size:1.6rem;font-weight:800;">{n_sim_green}</div>
            <div style="color:var(--text-secondary);font-size:0.75rem;font-weight:600;">ZONES SAFE</div>
        </div>
    </div>
    """, unsafe_allow_html=True)


# ─── Footer ─────────────────────────────────────────────────────────────────
st.markdown("""
<div style="text-align:center;padding:30px 0 10px 0;color:var(--text-muted);font-size:0.75rem;">
    Eco-Tide Production GeoAI Engine · Live Open-Meteo & Copernicus Ingest · SARIMAX & Hydrodynamic Physics
</div>
""", unsafe_allow_html=True)
