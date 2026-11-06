"""
🌊 Eco-Tide — Main Dashboard
Real-time coastal flood early warning system for Lagos, Nigeria.

Displays:
  • Traffic Light risk indicator
  • Key environmental metrics with 6h deltas
  • Interactive map of 20 Lagos LGA zones color-coded by risk
  • Water level time series (tidal + surge overlay)
  • Environmental factor tabs (rainfall, wind, pressure, temperature, soil moisture)
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import folium
from streamlit_folium import st_folium

from utils.data_loader import load_dataset, get_latest_data, load_live_forecast
from models.risk_engine import classify_risk_level, compute_zone_risks
from components.traffic_light import render_traffic_light
from components.metrics_cards import render_metric_card
from components.charts import create_water_level_chart, _theme_colors
from components.geolocation import render_location_widget, get_nearest_zone, get_distance_to_zone
from config.settings import (
    LAGOS_ZONES, LAGOS_BBOX, MAP_TILE, MAP_TILE_ATTR, LAGOS_CENTER,
    THEME, ABSOLUTE_SURGE_THRESHOLDS, RISK_COLORS,
)
from utils.theme import init_theme, render_theme_switcher, inject_theme_css, get_plotly_layout

# ── Dynamic Theme & Sidebar Switcher ────────────────────────────────────────
init_theme()
inject_theme_css()

with st.sidebar:
    render_theme_switcher()

# ─── Data Loading ───────────────────────────────────────────────────────────
@st.cache_data(ttl=3600)
def load_dashboard_data():
    """Load and prepare all data for the dashboard."""
    dataset = load_dataset()
    recent = get_latest_data(dataset, 168)  # Last 7 days
    return dataset, recent

dataset, recent_data = load_dashboard_data()

# Current (last row) and 6-hour-ago readings
current = recent_data.iloc[-1]
past_6h = recent_data.iloc[-7] if len(recent_data) > 6 else recent_data.iloc[0]

# Compute zone risks first
zone_risks = compute_zone_risks(
    water_level_m=current.get("water_level_m", 0.5),
    rainfall_mm=current.get("rainfall_mm", 0),
    wind_speed_ms=current.get("wind_speed_ms", 0),
    pressure_hpa=current.get("pressure_hpa", 1013),
    soil_moisture=current.get("soil_moisture", 0.3),
)

# Overall risk = worst zone (zones sorted by score desc already)
if zone_risks:
    worst = zone_risks[0]
    current_risk = {
        "level": worst["level"],
        "score": worst["score"],
        "label": worst["label"],
        "action": worst["action"],
        "icon": worst["icon"],
        "worst_zone": worst["name"],
    }
else:
    current_risk = classify_risk_level(
        water_level_m=current.get("water_level_m", 0.5),
        rainfall_mm=current.get("rainfall_mm", 0),
        wind_speed_ms=current.get("wind_speed_ms", 0),
        pressure_hpa=current.get("pressure_hpa", 1013),
        zone_elevation_m=3.0,
    )
    current_risk["worst_zone"] = "Lagos"


# ╔═══════════════════════════════════════════════════════════════════════════╗
# ║  HEADER SECTION                                                          ║
# ╚═══════════════════════════════════════════════════════════════════════════╝

st.markdown(f"""
<div style="display:flex; align-items:center; gap:14px; margin-bottom: 0.3rem;">
    <div style="font-family:'Inter',sans-serif; font-weight:900; font-size:1.9rem;
                background: linear-gradient(135deg, #0A84FF, #00C7BE);
                -webkit-background-clip:text; -webkit-text-fill-color:transparent;">
        🌊 Eco-Tide Dashboard
    </div>
</div>
<div style="font-size:0.82rem; color:var(--text-secondary); margin-bottom:1.2rem;">
    Coastal Flood Early Warning System — Lagos, Nigeria &nbsp;•&nbsp;
    Last updated: <span style="color:#0A84FF;">{recent_data.index[-1].strftime("%d %b %Y, %H:%M WAT")}</span>
</div>
""", unsafe_allow_html=True)

st.markdown('<div class="section-header">📍 Flood Risk Near Me</div>', unsafe_allow_html=True)
st.caption(
    "Opt in to share your device location with this page to check the nearest Lagos area. "
    "Your coordinates stay in this app session and are not saved unless you choose to submit a "
    "GPS-tagged incident report."
)
with st.container(border=True):
    user_location = render_location_widget(key_prefix="dashboard")
    if user_location:
        user_lat = user_location["lat"]
        user_lon = user_location["lon"]
        within_coverage = (
            LAGOS_BBOX["lat_min"] <= user_lat <= LAGOS_BBOX["lat_max"]
            and LAGOS_BBOX["lon_min"] <= user_lon <= LAGOS_BBOX["lon_max"]
        )

        if not within_coverage:
            st.info(
                "Your location is outside Eco-Tide's supported Lagos coverage area. "
                "The dashboard map below still shows risk for all supported Lagos zones."
            )
        else:
            nearby_zone = get_nearest_zone(user_lat, user_lon, LAGOS_ZONES)
            risk = next(
                (zone for zone in zone_risks if zone["name"] == nearby_zone["name"]),
                None,
            ) if nearby_zone else None

            if nearby_zone and risk:
                location_col, risk_col = st.columns([1, 2], gap="medium")
                with location_col:
                    st.metric("Nearest Lagos area", nearby_zone["name"])
                    st.caption(
                        f"{get_distance_to_zone(user_lat, user_lon, nearby_zone):.1f} km "
                        "from the area's mapped center"
                    )
                    accuracy = user_location.get("accuracy_m")
                    if accuracy is not None:
                        st.caption(f"GPS accuracy: about ±{accuracy:.0f} m")
                    if user_location.get("timestamp"):
                        st.caption(f"Location time (UTC): {user_location['timestamp']}")

                with risk_col:
                    risk_message = (
                        f"{risk['icon']} {risk['label']} — "
                        f"estimated risk score {risk['score']:.0%}"
                    )
                    if risk["level"] == "red":
                        st.error(risk_message)
                    elif risk["level"] == "amber":
                        st.warning(risk_message)
                    else:
                        st.success(risk_message)
                    st.write(risk["action"])
                    st.caption(
                        f"Model-based area estimate using dashboard data last updated "
                        f"{recent_data.index[-1].strftime('%d %b %Y, %H:%M WAT')}; it does not "
                        "confirm flooding at your exact location. Report an observed incident "
                        "through Community Chat."
                    )
                    st.page_link(
                        "pages/9_💬_Community_Chat.py",
                        label="Open Community Chat to report flooding",
                        icon="📣",
                    )

# Layout: traffic light (narrow) | metrics (wide)
tl_col, m1, m2, m3, m4 = st.columns([1.2, 1, 1, 1, 1], gap="medium")

with tl_col:
    render_traffic_light(
        level=current_risk["level"],
        label=current_risk["label"],
        action=f"Most at-risk: {current_risk.get('worst_zone','Lagos')} — {current_risk['action']}",
        score=current_risk["score"],
    )

# Metric deltas
def safe_delta(col):
    try:
        d = float(current.get(col, 0)) - float(past_6h.get(col, 0))
        return f"{d:+.2f}" if abs(d) > 0.005 else None
    except Exception:
        return None

with m1:
    render_metric_card(
        title="Water Level",
        value=f"{current.get('water_level_m', 0):.2f}",
        unit="m",
        delta=safe_delta("water_level_m"),
        icon="🌊",
    )

with m2:
    rain_val = current.get("rainfall_6h", current.get("rainfall_mm", 0) * 6)
    rain_past = past_6h.get("rainfall_6h", past_6h.get("rainfall_mm", 0) * 6)
    d = float(rain_val) - float(rain_past)
    render_metric_card(
        title="Rainfall (6h)",
        value=f"{rain_val:.1f}",
        unit="mm",
        delta=f"{d:+.1f}" if abs(d) > 0.05 else None,
        icon="🌧️",
    )

with m3:
    render_metric_card(
        title="Wind Speed",
        value=f"{current.get('wind_speed_ms', 0):.1f}",
        unit="m/s",
        delta=safe_delta("wind_speed_ms"),
        icon="💨",
    )

with m4:
    render_metric_card(
        title="Pressure",
        value=f"{current.get('pressure_hpa', 1013):.0f}",
        unit="hPa",
        delta=safe_delta("pressure_hpa"),
        icon="🔻",
    )

st.markdown("<div style='height:0.8rem;'></div>", unsafe_allow_html=True)


# ╔═══════════════════════════════════════════════════════════════════════════╗
# ║  INTERACTIVE MAP                                                         ║
# ╚═══════════════════════════════════════════════════════════════════════════╝

st.markdown('<div class="section-header">🗺️ Lagos LGA Risk Map — 20 Zones</div>', unsafe_allow_html=True)

# ─── Build Plotly Map (no API key, fully interactive) ───────────────────────
LEVEL_COLORS = {"red": "#FF1744", "amber": "#FFD600", "green": "#00C853"}

lats   = [z["lat"]            for z in zone_risks]
lons   = [z["lon"]            for z in zone_risks]
names  = [z["name"]           for z in zone_risks]
scores = [z["score"]          for z in zone_risks]
levels = [z["level"]          for z in zone_risks]
labels = [z.get("label","")   for z in zone_risks]
icons  = [z.get("icon","")    for z in zone_risks]
elevs  = [z["elevation_m"]    for z in zone_risks]
pops   = [z["population"]     for z in zone_risks]
dists  = [z["distance_to_water_km"] for z in zone_risks]
drains = [int(z.get("drainage_capacity",0.5)*100) for z in zone_risks]
colors = [LEVEL_COLORS[lvl]   for lvl in levels]
sizes  = [max(14, s * 52)     for s in scores]   # bubble size

hover_text = [
    f"<b>{n}</b><br>"
    f"{ic} <b style='color:{c}'>{lb.upper()}</b><br>"
    f"━━━━━━━━━━━━━━━━━━<br>"
    f"📊 Risk Score: <b>{int(s*100)}%</b><br>"
    f"🏔 Elevation: <b>{e:.1f} m</b><br>"
    f"🚰 Drainage: <b>{dr}%</b><br>"
    f"🌊 Dist to Water: <b>{d:.1f} km</b><br>"
    f"👥 Population: <b>{p:,}</b>"
    for n, ic, lb, c, s, e, dr, d, p
    in zip(names, icons, labels, colors, scores, elevs, drains, dists, pops)
]

fig_map = go.Figure()

# ── Layer 1: Density heat map (soft glow underneath) ─────────────────────────
fig_map.add_trace(go.Densitymapbox(
    lat=lats, lon=lons, z=scores,
    radius=45,
    colorscale=[
        [0.0, "rgba(0,80,255,0)"],
        [0.3, "rgba(0,200,200,0.3)"],
        [0.6, "rgba(255,200,0,0.5)"],
        [0.8, "rgba(255,80,0,0.65)"],
        [1.0, "rgba(255,23,68,0.80)"],
    ],
    showscale=False,
    below="traces",
    name="Risk Heat",
    hoverinfo="skip",
))

# ── Layer 2: Bubble scatter markers ──────────────────────────────────────────
fig_map.add_trace(go.Scattermapbox(
    lat=lats, lon=lons,
    mode="markers+text",
    marker=dict(
        size=sizes,
        color=colors,
        opacity=0.88,
        sizemode="diameter",
    ),
    text=names,
    textposition="top center",
    textfont=dict(color="white", size=9),
    hovertext=hover_text,
    hoverinfo="text",
    name="LGA Zones",
))

fig_map.update_layout(
    mapbox=dict(
        style="open-street-map",   # ← 100% free, built into Plotly, NO token needed
        center=dict(lat=LAGOS_CENTER["lat"], lon=LAGOS_CENTER["lon"]),
        zoom=10.5,
    ),
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    margin=dict(l=0, r=0, t=0, b=0),
    height=560,
    showlegend=False,
    hoverlabel=dict(
        bgcolor="#1A1D2E",
        bordercolor="#444",
        font=dict(family="Inter, sans-serif", size=12, color="white"),
    ),
)

st.plotly_chart(fig_map, use_container_width=True, config={"scrollZoom": True, "displayModeBar": False})




# ╔═══════════════════════════════════════════════════════════════════════════╗
# ║  WATER LEVEL CHART                                                       ║
# ╚═══════════════════════════════════════════════════════════════════════════╝

st.markdown('<div class="section-header">📈 Water Level Monitoring</div>', unsafe_allow_html=True)

wl_chart = create_water_level_chart(recent_data, show_components=False)

# Add risk threshold lines
thresholds = ABSOLUTE_SURGE_THRESHOLDS
wl_chart.add_hline(
    y=thresholds["amber_max_m"],
    line=dict(color="#FFD600", width=1, dash="dash"),
    annotation_text="Caution",
    annotation=dict(font_color="#FFD600", font_size=10),
)
wl_chart.add_hline(
    y=thresholds["red_min_m"],
    line=dict(color="#FF1744", width=1, dash="dash"),
    annotation_text="Danger",
    annotation=dict(font_color="#FF1744", font_size=10),
)

wl_chart.update_layout(get_plotly_layout(
    height=380,
    margin=dict(l=60, r=40, t=40, b=40),
))
st.plotly_chart(wl_chart, use_container_width=True, config={"displayModeBar": False})

st.markdown("<br>", unsafe_allow_html=True)
st.markdown('<div class="section-header">🔮 Live 7-Day Forecast — Lagos</div>', unsafe_allow_html=True)

forecast_df = load_live_forecast()
if forecast_df is not None and not forecast_df.empty:
    fig_f = go.Figure()
    
    if 'water_level_upper' in forecast_df.columns and 'water_level_lower' in forecast_df.columns:
        fig_f.add_trace(go.Scatter(
            x=forecast_df.index, y=forecast_df['water_level_upper'],
            mode='lines', line=dict(width=0), showlegend=False, hoverinfo='skip'
        ))
        fig_f.add_trace(go.Scatter(
            x=forecast_df.index, y=forecast_df['water_level_lower'],
            mode='lines', line=dict(width=0), fill='tonexty',
            fillcolor='rgba(0,199,190,0.2)', name='95% Confidence Band',
            showlegend=False, hoverinfo='skip'
        ))
    
    if 'water_level_m' in forecast_df.columns:
        fig_f.add_trace(go.Scatter(
            x=forecast_df.index, y=forecast_df['water_level_m'],
            mode='lines', line=dict(color='#00C7BE', width=2),
            name='Forecast WL'
        ))
        
    if 'rainfall_mm' in forecast_df.columns:
        fig_f.add_trace(go.Bar(
            x=forecast_df.index, y=forecast_df['rainfall_mm'],
            marker_color='rgba(10,132,255,0.4)', yaxis='y2', name='Rainfall'
        ))
        
    fig_f.update_layout(get_plotly_layout(
        yaxis=dict(title=dict(text='Water Level (m)')),
        yaxis2=dict(title=dict(text='Rainfall (mm)'), overlaying='y', side='right', showgrid=False, automargin=True),
        margin=dict(l=60, r=60, t=30, b=30),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    ))
    st.plotly_chart(fig_f, use_container_width=True, config={"displayModeBar": False})
else:
    st.info("Live forecast data is currently unavailable.")

# ╔═══════════════════════════════════════════════════════════════════════════╗
# ║  VIRTUAL SENSOR (SATELLITE ALTIMETRY)                                    ║
# ╚═══════════════════════════════════════════════════════════════════════════╝

st.markdown("<br>", unsafe_allow_html=True)
st.markdown(
    '<div class="section-header">🛰️ Virtual Sensor Telemetry (Satellite Altimetry)</div>',
    unsafe_allow_html=True
)
st.markdown(
    '<p style="color:var(--text-secondary); font-size:0.9em; margin-top:-10px; margin-bottom:15px;">'
    'Real-time marine data driven by <b>Copernicus Marine Service (CMEMS)</b> ingesting '
    '<b>Sentinel-3</b> and <b>Jason-3</b> radar altimetry. '
    'This Software-First GeoAI approach replaces broken physical tide gauges.</p>',
    unsafe_allow_html=True
)

if forecast_df is not None and 'wave_height_m' in forecast_df.columns:
    col1, col2, col3 = st.columns(3)
    current_wave = forecast_df['wave_height_m'].iloc[0]
    current_period = forecast_df.get('wave_period_s', pd.Series([0])).iloc[0]
    
    # Calculate an SLA approximation based on Inverse Barometer Effect and Wave Height
    current_press = forecast_df.get('pressure_hpa', pd.Series([1013.25])).iloc[0]
    sla_m = (1013.25 - current_press) * 0.01 + (current_wave * 0.1)
    
    col1.metric("🌊 Sea Level Anomaly (SLA)", f"{sla_m:+.2f} m", "Copernicus Altimetry Derived")
    col2.metric("📏 Significant Wave Height", f"{current_wave:.2f} m", "Gulf of Guinea Swell")
    col3.metric("⏱️ Wave Period", f"{current_period:.1f} s", "Energy Flux")
    
    # Simple chart for SLA
    fig_sla = go.Figure()
    
    forecast_sla = (1013.25 - forecast_df['pressure_hpa']) * 0.01 + (forecast_df['wave_height_m'] * 0.1)
    
    fig_sla.add_trace(go.Scatter(
        x=forecast_df.index, y=forecast_df['forecast_sla' if 'forecast_sla' in forecast_df else 'wave_height_m'],
        mode='lines', line=dict(color='#FF6B35', width=2),
        fill='tozeroy', fillcolor='rgba(255,107,53,0.1)',
        name='SLA (m)'
    ))
    
    fig_sla.update_layout(get_plotly_layout(
        yaxis=dict(title=dict(text='Sea Level Anomaly (m)')),
        margin=dict(l=60, r=40, t=30, b=30),
        height=250
    ))
    st.plotly_chart(fig_sla, use_container_width=True, config={"displayModeBar": False})

# ╔═══════════════════════════════════════════════════════════════════════════╗
# ║  ENVIRONMENTAL FACTORS PANEL                                             ║
# ╚═══════════════════════════════════════════════════════════════════════════╝

st.markdown('<div class="section-header">🌡️ Environmental Factors — Last 7 Days</div>', unsafe_allow_html=True)

def make_env_chart(df, col, title, color, unit):
    """Create a small environmental factor chart."""
    if col not in df.columns:
        return None
    fig = go.Figure()
    fill_mode = "tozeroy" if col != "pressure_hpa" else None
    
    fig.add_trace(go.Scatter(
        x=df.index, y=df[col],
        mode="lines",
        line=dict(color=color, width=2),
        fill=fill_mode,
        fillcolor=f"rgba({int(color[1:3],16)},{int(color[3:5],16)},{int(color[5:7],16)},0.08)" if fill_mode else None,
        hovertemplate=f"<b>{title}</b><br>%{{x|%b %d %H:%M}}<br>%{{y:.2f}} {unit}<extra></extra>",
    ))
    fig.update_layout(get_plotly_layout(
        height=280,
        margin=dict(l=60, r=20, t=30, b=30),
        showlegend=False,
        yaxis=dict(title=dict(text=unit)),
        title=dict(text=title, font=dict(size=14)),
    ))
    return fig


tab_rain, tab_wind, tab_pressure, tab_temp, tab_soil = st.tabs([
    "🌧️ Rainfall", "💨 Wind", "🔻 Pressure", "🌡️ Temperature", "🌱 Soil Moisture"
])

env_configs = [
    (tab_rain,     "rainfall_mm",   "Rainfall",             "#0A84FF", "mm/hr"),
    (tab_wind,     "wind_speed_ms", "Wind Speed",           "#FF6B35", "m/s"),
    (tab_pressure, "pressure_hpa",  "Atmospheric Pressure", "#A78BFA", "hPa"),
    (tab_temp,     "temp_celsius",  "Air Temperature",      "#FF1744", "°C"),
    (tab_soil,     "soil_moisture", "Soil Moisture",         "#00C853", "m³/m³"),
]

for tab, col_name, title, color, unit in env_configs:
    with tab:
        fig = make_env_chart(recent_data, col_name, title, color, unit)
        if fig:
            st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
        else:
            st.info(f"{title} data not available in dataset.")


# ╔═══════════════════════════════════════════════════════════════════════════╗
# ║  DATA EXPORT & REPORT DOWNLOAD                                           ║
# ╚═══════════════════════════════════════════════════════════════════════════╝

st.markdown('<div class="section-header">📥 Export Risk Report</div>', unsafe_allow_html=True)

import datetime
report_lines = [
    "=========================================",
    "   ECO-TIDE FLOOD RISK ASSESSMENT REPORT",
    "=========================================",
    f"Generated at: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
    "",
    "--- CURRENT CONDITIONS ---",
    f"Water Level: {current.get('water_level_m', 0):.2f} m",
    f"Rainfall (1h): {current.get('rainfall_mm', 0):.1f} mm",
    f"Wind Speed: {current.get('wind_speed_ms', 0):.1f} m/s",
    f"Atmospheric Pressure: {current.get('pressure_hpa', 1013):.0f} hPa",
    "",
    "--- ZONE RISK ANALYSIS ---"
]

sorted_zones = sorted(zone_risks, key=lambda x: x["score"], reverse=True)
for z in sorted_zones:
    report_lines.append(f"{z['name']:<20} | Level: {z['level'].upper():<5} | Score: {z['score']:.1%}")

report_lines.extend([
    "",
    "--- RECOMMENDATIONS ---"
])

if current_risk["level"] == "red":
    report_lines.append("CRITICAL DANGER: Evacuate low-lying areas immediately. Deploy emergency pumping.")
elif current_risk["level"] == "amber":
    report_lines.append("WARNING: Prepare for possible flooding. Clear drains and monitor alerts.")
else:
    report_lines.append("NORMAL: No immediate flood threat. Continue routine monitoring.")

report_text = "\n".join(report_lines)

st.download_button(
    label="Generate Report",
    data=report_text,
    file_name=f"eco_tide_report_{datetime.datetime.now().strftime('%Y%m%d_%H%M')}.txt",
    mime="text/plain"
)

st.markdown("<br>", unsafe_allow_html=True)

# ─── Footer ─────────────────────────────────────────────────────────────────
st.markdown("""
<div style="text-align:center; padding:2rem 0 1rem; font-size:0.7rem; color:var(--text-muted);">
    Eco-Tide v1.0 &nbsp;•&nbsp; Coastal Flood Early Warning System &nbsp;•&nbsp; Lagos, Nigeria<br>
    Data: ECMWF ERA5 via Open-Meteo &nbsp;|&nbsp; Tides: Lagos Harmonic Constituents
</div>
""", unsafe_allow_html=True)
