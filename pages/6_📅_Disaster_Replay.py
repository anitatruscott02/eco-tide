"""
📅 Eco-Tide — Historical Disaster Replay
Replay and analyze past extreme flood events in Lagos.
"""

import sys
import os

if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from datetime import datetime

from utils.data_loader import load_dataset
from models.risk_engine import classify_risk_level
from config.settings import ABSOLUTE_SURGE_THRESHOLDS, THEME
from utils.theme import init_theme, render_theme_switcher, inject_theme_css, get_plotly_layout

# ── Dynamic Theme & Sidebar Switcher ────────────────────────────────────────
init_theme()
inject_theme_css()

with st.sidebar:
    render_theme_switcher()

# ─── Page Header ────────────────────────────────────────────────────────────
st.markdown("""
<div style="font-family:'Inter',sans-serif; font-weight:900; font-size:1.9rem;
            background: linear-gradient(135deg, #FF1744, #FF6B35);
            -webkit-background-clip:text; -webkit-text-fill-color:transparent;
            margin-bottom: 4px;">
    📅 Historical Disaster Replay
</div>
<div style="font-size:0.95rem; color:var(--text-secondary); margin-bottom:1.5rem;">
    Replay past extreme flood events in Lagos to prove Eco-Tide would have predicted them.
</div>
""", unsafe_allow_html=True)

# ─── Load Data ──────────────────────────────────────────────────────────────
dataset = load_dataset()
data_start = dataset.index.min()
data_end = dataset.index.max()

# ─── Event Definitions (aligned to our actual dataset range) ────────────────
EVENTS = {
    "October 2022 — Nationwide Floods": {
        "start": "2022-10-01",
        "end": "2022-10-20",
        "desc": "Part of the devastating 2022 Nigeria floods — the worst in a decade. "
                "Intense rainfall combined with river overflow and high coastal tides submerged "
                "major parts of Lagos, Bayelsa, Anambra, and Kogi states. Over 600 people died "
                "and 1.3 million were displaced nationwide.",
        "severity": "CATASTROPHIC",
        "severity_color": "#FF1744",
    },
    "June 2023 — Early Wet Season Surge": {
        "start": "2023-06-15",
        "end": "2023-07-05",
        "desc": "Severe early wet-season flooding that submerged several low-lying zones "
                "across Lagos. Flash floods in Lekki, Ajah, and Ibeju-Lekki exposed critical "
                "drainage vulnerabilities and waste management failures.",
        "severity": "SEVERE",
        "severity_color": "#FF6B35",
    },
    "July 2024 — Mid-Season Peak": {
        "start": "2024-07-01",
        "end": "2024-07-20",
        "desc": "Peak wet season flooding driven by sustained heavy rainfall, high soil "
                "saturation, and spring tides. Multiple LGAs reported waterlogged roads and "
                "property damage.",
        "severity": "HIGH",
        "severity_color": "#FFD600",
    },
    "September 2025 — Late Season Compound Event": {
        "start": "2025-09-01",
        "end": "2025-09-15",
        "desc": "A compound flooding event where heavy rainfall, low atmospheric pressure, "
                "strong onshore winds, and near-spring tides aligned simultaneously — "
                "the exact scenario Eco-Tide is designed to detect and warn about.",
        "severity": "SEVERE",
        "severity_color": "#FF6B35",
    },
    "Custom Date Range": {
        "start": None,
        "end": None,
        "desc": "Select your own date range to analyze.",
        "severity": "CUSTOM",
        "severity_color": "#0A84FF",
    },
}

# ─── Event Selector ─────────────────────────────────────────────────────────
selected_event = st.selectbox("Select Historical Event", list(EVENTS.keys()))
event = EVENTS[selected_event]

if selected_event == "Custom Date Range":
    col_s, col_e = st.columns(2)
    start_date = col_s.date_input("Start Date", value=data_start.date())
    end_date = col_e.date_input("End Date", value=data_end.date())
    event_desc = "Custom user-selected date range for analysis."
    severity = "CUSTOM"
    severity_color = "#0A84FF"
else:
    start_date = pd.to_datetime(event["start"]).date()
    end_date = pd.to_datetime(event["end"]).date()
    event_desc = event["desc"]
    severity = event["severity"]
    severity_color = event["severity_color"]

# Event description card
st.markdown(f"""
<div style="background: rgba(255,23,68,0.05); border-left: 4px solid {severity_color};
            padding: 16px; border-radius: 8px; margin-bottom: 20px;">
    <div style="display:flex; align-items:center; gap:10px; margin-bottom:8px;">
        <span style="background:{severity_color}; color:white; padding:3px 10px; border-radius:12px;
                     font-size:0.75rem; font-weight:700;">{severity}</span>
        <span style="font-weight:700; font-size:1.05rem;">{selected_event}</span>
    </div>
    <div style="font-size:0.9rem; color:var(--text-secondary); line-height:1.5;">{event_desc}</div>
</div>
""", unsafe_allow_html=True)

# ─── Filter Data ────────────────────────────────────────────────────────────
start_dt = pd.to_datetime(start_date)
end_dt = pd.to_datetime(end_date) + pd.Timedelta(days=1) - pd.Timedelta(seconds=1)

mask = (dataset.index >= start_dt) & (dataset.index <= end_dt)
filtered = dataset.loc[mask].copy()

if filtered.empty:
    st.error(f"No data available for {start_date} to {end_date}. "
             f"Our dataset covers {data_start.strftime('%Y-%m-%d')} to {data_end.strftime('%Y-%m-%d')}.")
    st.stop()

# ─── Compute Hourly Risk ───────────────────────────────────────────────────
# Use the most vulnerable zone parameters (Ibeju-Lekki: 1m elevation, poor drainage)
# This accurately reflects what happens during real flood events
from config.settings import LAGOS_ZONES
vulnerable_zone = min(LAGOS_ZONES, key=lambda z: z["elevation_m"])

st.markdown(f"""
<div style="background:rgba(10,132,255,0.05); border-left:3px solid #0A84FF;
            padding:10px 14px; border-radius:6px; margin-bottom:16px; font-size:0.85rem;">
    🎯 <b>Analyzing risk for most vulnerable zone:</b> {vulnerable_zone['name']} 
    (Elevation: {vulnerable_zone['elevation_m']}m, Drainage: {int(vulnerable_zone.get('drainage_capacity', 0.5)*100)}%)
</div>
""", unsafe_allow_html=True)

risk_scores = []
risk_levels = []
for _, row in filtered.iterrows():
    risk = classify_risk_level(
        water_level_m=row.get("water_level_m", 0.5),
        rainfall_mm=row.get("rainfall_mm", 0),
        wind_speed_ms=row.get("wind_speed_ms", 0),
        pressure_hpa=row.get("pressure_hpa", 1013),
        zone_elevation_m=vulnerable_zone["elevation_m"],
        zone_drainage_capacity=vulnerable_zone.get("drainage_capacity", 0.3),
        soil_moisture=row.get("soil_moisture", 0.5),
        distance_to_water_km=vulnerable_zone.get("distance_to_water_km", 0.5),
    )
    risk_scores.append(risk["score"])
    risk_levels.append(risk["level"])

filtered["risk_score"] = risk_scores
filtered["risk_level"] = risk_levels

# ─── Key Metrics ────────────────────────────────────────────────────────────
st.markdown('<div style="font-weight:700; font-size:1.1rem; margin-bottom:10px;">📊 Event Summary</div>',
            unsafe_allow_html=True)

m1, m2, m3, m4, m5 = st.columns(5)
max_wl = filtered["water_level_m"].max()
peak_rain = filtered["rainfall_mm"].max()
max_wind = filtered["wind_speed_ms"].max()
min_press = filtered["pressure_hpa"].min()
max_risk = filtered["risk_score"].max()
red_hours = len(filtered[filtered["risk_level"] == "red"])

m1.metric("🌊 Peak Water Level", f"{max_wl:.2f} m")
m2.metric("🌧️ Peak Rainfall", f"{peak_rain:.1f} mm/h")
m3.metric("💨 Max Wind", f"{max_wind:.1f} m/s")
m4.metric("🔻 Min Pressure", f"{min_press:.0f} hPa")
m5.metric("🔴 Red Alert Hours", f"{red_hours}")

st.markdown("<br>", unsafe_allow_html=True)

# ─── Water Level & Rainfall Chart ───────────────────────────────────────────
st.markdown('<div style="font-weight:700; font-size:1.1rem; margin-bottom:10px;">🌊 Water Level & Rainfall Timeline</div>',
            unsafe_allow_html=True)

fig = go.Figure()

# Rainfall bars (secondary axis)
fig.add_trace(go.Bar(
    x=filtered.index, y=filtered["rainfall_mm"],
    name="Rainfall (mm/h)", marker_color="rgba(10,132,255,0.35)",
    yaxis="y2",
    hovertemplate="<b>Rainfall</b><br>%{x|%b %d %H:%M}<br>%{y:.1f} mm/h<extra></extra>",
))

# Water level line
fig.add_trace(go.Scatter(
    x=filtered.index, y=filtered["water_level_m"],
    name="Water Level (m)", line=dict(color="#0A84FF", width=2),
    fill="tozeroy", fillcolor="rgba(10,132,255,0.08)",
    hovertemplate="<b>Water Level</b><br>%{x|%b %d %H:%M}<br>%{y:.3f} m<extra></extra>",
))

# Danger thresholds
fig.add_hline(y=ABSOLUTE_SURGE_THRESHOLDS["amber_max_m"],
              line=dict(color="#FFD600", width=1, dash="dash"),
              annotation_text="Caution", annotation=dict(font_color="#FFD600", font_size=10))
fig.add_hline(y=ABSOLUTE_SURGE_THRESHOLDS["red_min_m"],
              line=dict(color="#FF1744", width=1, dash="dash"),
              annotation_text="Danger", annotation=dict(font_color="#FF1744", font_size=10))

# Peak surge marker
peak_idx = filtered["water_level_m"].idxmax()
fig.add_trace(go.Scatter(
    x=[peak_idx], y=[max_wl],
    mode="markers+text", marker=dict(color="#FF1744", size=12, symbol="star"),
    text=[f"Peak: {max_wl:.2f}m"], textposition="top center",
    textfont=dict(color="#FF1744", size=11, family="Inter"),
    showlegend=False,
))

fig.update_layout(get_plotly_layout(
    height=420,
    margin=dict(l=60, r=60, t=30, b=30),
    yaxis=dict(title="Water Level (m)"),
    yaxis2=dict(title="Rainfall (mm/h)", overlaying="y", side="right", showgrid=False),
    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    hovermode="x unified",
))
st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

# ─── Risk Evolution Timeline ───────────────────────────────────────────────
st.markdown('<div style="font-weight:700; font-size:1.1rem; margin-bottom:10px;">🚨 Risk Score Evolution</div>',
            unsafe_allow_html=True)

# Color-code by risk level
risk_colors = [
    "#FF1744" if s >= 0.6 else "#FFD600" if s >= 0.3 else "#00C853"
    for s in filtered["risk_score"]
]

fig_risk = go.Figure()

# Background zones
fig_risk.add_hrect(y0=0, y1=0.3, fillcolor="rgba(0,200,83,0.05)", line_width=0)
fig_risk.add_hrect(y0=0.3, y1=0.6, fillcolor="rgba(255,214,0,0.05)", line_width=0)
fig_risk.add_hrect(y0=0.6, y1=1.0, fillcolor="rgba(255,23,68,0.05)", line_width=0)

fig_risk.add_trace(go.Scatter(
    x=filtered.index, y=filtered["risk_score"],
    mode="lines", line=dict(color="#FF1744", width=2),
    fill="tozeroy", fillcolor="rgba(255,23,68,0.08)",
    name="Risk Score",
    hovertemplate="<b>Risk Score</b><br>%{x|%b %d %H:%M}<br>%{y:.1%}<extra></extra>",
))

# Threshold lines
fig_risk.add_hline(y=0.3, line=dict(color="#FFD600", width=1, dash="dot"),
                   annotation_text="Caution (30%)", annotation=dict(font_color="#FFD600", font_size=9))
fig_risk.add_hline(y=0.6, line=dict(color="#FF1744", width=1, dash="dot"),
                   annotation_text="Danger (60%)", annotation=dict(font_color="#FF1744", font_size=9))

fig_risk.update_layout(get_plotly_layout(
    height=300,
    margin=dict(l=60, r=40, t=20, b=30),
    yaxis=dict(title="Risk Score", range=[0, 1], tickformat=".0%"),
    showlegend=False,
))
st.plotly_chart(fig_risk, use_container_width=True, config={"displayModeBar": False})

# ─── Early Warning Historical Backtest & Validation ─────────────────────────────
st.markdown('<div style="font-weight:700; font-size:1.1rem; margin-bottom:10px;">🛡️ Early Warning Historical Backtest & Validation</div>',
            unsafe_allow_html=True)

red_alerts = filtered[filtered["risk_score"] >= 0.6]
peak_surge_idx = filtered["water_level_m"].idxmax()

if not red_alerts.empty:
    first_red = red_alerts.index[0]
    if first_red < peak_surge_idx:
        hours_advance = (peak_surge_idx - first_red).total_seconds() / 3600
        st.markdown(f"""
        <div style="background:rgba(0,200,83,0.08); border-left:4px solid #00C853;
                    padding:16px; border-radius:8px;">
            <div style="font-weight:700; color:#00C853; font-size:1.05rem; margin-bottom:6px;">
                ✅ Eco-Tide Would Have Saved Lives
            </div>
            <div style="font-size:0.95rem; line-height:1.6;">
                If Eco-Tide had been active during this event, it would have issued a 
                <b style="color:#FF1744;">RED ALERT {hours_advance:.0f} hours before</b> the peak surge 
                occurred at {peak_surge_idx.strftime('%B %d, %Y %H:%M')}.<br><br>
                That is <b>{hours_advance:.0f} hours of advance warning</b> for LASEMA to activate 
                emergency protocols, evacuate vulnerable communities, and pre-position rescue assets.
            </div>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.warning("⚠️ The peak surge occurred very rapidly. Eco-Tide would have issued a concurrent RED ALERT.")
else:
    amber_alerts = filtered[filtered["risk_score"] >= 0.3]
    if not amber_alerts.empty:
        st.info(f"🟡 Eco-Tide would have issued **AMBER (Caution) alerts** during this period "
                f"({len(amber_alerts)} hours at elevated risk), but conditions did not reach the RED threshold.")
    else:
        st.success("✅ Conditions during this period remained within safe limits. No alerts would have been triggered.")
