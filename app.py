"""
Eco-Tide | Coastal Flood Early Warning System for Lagos, Nigeria
Main Streamlit Application Entry Point
"""

import sys
import os
import streamlit as st

# ── Ensure project root is on the path ──────────────────────────────────────
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config.settings import THEME, LAGOS_ZONES, RISK_COLORS
from utils.data_loader import load_dataset, get_latest_data, get_data_summary
from models.risk_engine import classify_risk_level, get_current_risk_summary
from components.traffic_light import render_traffic_light
from utils.theme import init_theme, render_theme_switcher, inject_theme_css

# ── Page Config ─────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Eco-Tide | Coastal Flood EWS",
    page_icon="🌊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Dynamic Theme & High-Contrast CSS ───────────────────────────────────────
active_theme = init_theme()
inject_theme_css()

# ── Sidebar ─────────────────────────────────────────────────────────────────
with st.sidebar:
    render_theme_switcher()

    # ── App Brand Header ────────────────────────────────────────────────────
    st.markdown("""
        <div style="padding: 0 0 10px 0;">
            <div style="font-size: 32px; margin-bottom: 2px;">🌊</div>
            <div class="sidebar-logo">Eco-Tide</div>
            <div style="font-size: 13px; font-weight: 500; color: var(--text-secondary); letter-spacing: 0.4px;">
                Coastal Flood Early Warning System
            </div>
        </div>
    """, unsafe_allow_html=True)

    st.markdown('<div class="eco-divider"></div>', unsafe_allow_html=True)

    # ── Data Status ─────────────────────────────────────────────────────────
    try:
        dataset = load_dataset()
        summary = get_data_summary(dataset)
        data_loaded = True
    except Exception:
        dataset = None
        summary = None
        data_loaded = False

    if data_loaded:
        st.markdown("""
            <div class="sidebar-status">
                <span style="font-size:12px;">●</span> Dataset Loaded
            </div>
        """, unsafe_allow_html=True)

        st.markdown(f"""
            <div style="padding: 4px 0;">
                <div class="sidebar-stat"><span class="ss-label">Records</span>
                    <span class="ss-value">{summary['total_records']:,}</span></div>
                <div class="sidebar-stat"><span class="ss-label">Features</span>
                    <span class="ss-value">{summary['n_features']}</span></div>
                <div class="sidebar-stat"><span class="ss-label">From</span>
                    <span class="ss-value">{summary['date_range_start']}</span></div>
                <div class="sidebar-stat"><span class="ss-label">To</span>
                    <span class="ss-value">{summary['date_range_end']}</span></div>
                <div class="sidebar-stat"><span class="ss-label">Missing</span>
                    <span class="ss-value">{summary['missing_pct']:.1f}%</span></div>
            </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown("""
            <div class="sidebar-status offline">
                <span style="font-size:10px;">●</span> No dataset loaded
            </div>
        """, unsafe_allow_html=True)
        st.info("Run `data/fetch_real_data.py` to download and process the Lagos dataset.")

    st.markdown('<div class="eco-divider"></div>', unsafe_allow_html=True)

    st.markdown("""
        <div style="padding: 4px 0;">
            <div style="font-size: 11px; font-weight: 700; color: var(--text-muted);
                        letter-spacing: 0.8px; text-transform: uppercase; margin-bottom: 8px;">
                Data Sources
            </div>
            <div style="font-size: 13px; font-weight: 500; color: var(--text-secondary); line-height: 2;">
                🌤️ <a href="https://open-meteo.com" target="_blank"
                       style="color: var(--primary); text-decoration: none; font-weight: 600;">Open-Meteo Weather</a><br>
                🌊 <a href="https://uhslc.soest.hawaii.edu" target="_blank"
                       style="color: var(--secondary); text-decoration: none; font-weight: 600;">UHSLC Tide Gauges</a><br>
                🛰️ <a href="https://open-meteo.com/en/docs/marine-weather-api" target="_blank"
                       style="color: var(--accent); text-decoration: none; font-weight: 600;">Open-Meteo Marine</a>
            </div>
        </div>
    """, unsafe_allow_html=True)

    st.markdown('<div class="eco-divider"></div>', unsafe_allow_html=True)

    st.markdown("""
        <div style="font-size: 11px; font-weight: 500; color: var(--text-muted); text-align: center; padding-top: 4px;">
            Eco-Tide v1.0 &middot; Lagos, Nigeria<br>
            Software-First GeoAI early warning system
        </div>
    """, unsafe_allow_html=True)

# ── Main Content: Hero Section ──────────────────────────────────────────────
st.markdown("""
    <div style="margin-bottom: 24px;">
        <div class="hero-tag">🛰️ Real-Time Monitoring</div>
        <div class="hero-title" style="font-size: 48px; font-weight: 900; letter-spacing: -0.5px; margin-bottom: 8px;">Eco-Tide</div>
        <p class="hero-subtitle" style="font-size: 1.05rem; font-weight: 400; line-height: 1.65; max-width: 720px; color: var(--text-body);">
            AI-powered coastal flood early warning system for Lagos, Nigeria.
            Combines tidal harmonics, SARIMAX forecasting, and real-time environmental
            data to protect 24 million residents across 20 local government areas.
        </p>
    </div>
""", unsafe_allow_html=True)

st.markdown('<div class="eco-divider"></div>', unsafe_allow_html=True)

# ── Welcome & Mission Statement ──────────────────────────────────────────────
st.markdown("""
    <div class="glass-card" style="display: flex; flex-direction: column; gap: 20px; margin-bottom: 32px;">
        <div style="font-size: 20px; font-weight: 800; color: var(--text-primary); display: flex; align-items: center; gap: 10px;">
            🌍 The Mission: Protecting Lagos from the Rising Tide
        </div>
        <div style="font-size: 1.02rem; color: var(--text-body); line-height: 1.75;">
            Lagos is one of the most vulnerable coastal cities in the world, with large populations living less than 2 meters above sea level. Traditional early warning systems rely on physical tide gauges and sensors, which are frequently unmaintained, stolen, or broken, leaving millions in the dark.
            <br><br>
            <b style="color: var(--primary);">Eco-Tide takes a radically different approach: Software-First GeoAI.</b>
            <br><br>
            By leveraging satellite data from the European Space Agency's <b>Copernicus DEM</b>, open-source meteorological APIs, and advanced AI (SARIMAX), Eco-Tide operates entirely autonomously from space. It cannot be stolen, requires zero physical hardware maintenance, and delivers up to 72-hour advance warnings across all 20 Local Government Areas.
        </div>
        <div style="display: flex; gap: 14px; margin-top: 10px; flex-wrap: wrap;">
            <a href="/Dashboard" target="_self" style="text-decoration: none;">
                <div style="background: linear-gradient(135deg, var(--primary), var(--secondary)); color: #FFFFFF; padding: 12px 24px; border-radius: 10px; font-weight: 700; font-size: 14px; text-align: center; cursor: pointer; box-shadow: 0 4px 14px rgba(2, 132, 199, 0.35);">
                    🚀 Launch Dashboard
                </div>
            </a>
            <a href="/Methodology" target="_self" style="text-decoration: none;">
                <div style="background: var(--bg-card-hover); color: var(--text-primary); border: 1px solid var(--border-card); padding: 12px 24px; border-radius: 10px; font-weight: 700; font-size: 14px; text-align: center; cursor: pointer;">
                    📖 Read the Science
                </div>
            </a>
        </div>
    </div>
""", unsafe_allow_html=True)

# ── How It Works ────────────────────────────────────────────────────────────
st.markdown("""
    <div style="text-align: center; margin-bottom: 24px;">
        <span style="font-size: 13px; font-weight: 800; color: var(--primary);
                     letter-spacing: 1.2px; text-transform: uppercase;">
            HOW IT WORKS
        </span>
    </div>
""", unsafe_allow_html=True)

steps_cols = st.columns(4, gap="medium")
steps = [
    {
        "num": "STEP 01",
        "icon": "📡",
        "title": "Data Ingestion",
        "desc": "Real-time weather, marine, and tidal data ingested from Open-Meteo & UHSLC stations.",
    },
    {
        "num": "STEP 02",
        "icon": "🔬",
        "title": "Tidal Harmonics",
        "desc": "6-constituent harmonic analysis decomposes astronomical tides from storm surges.",
    },
    {
        "num": "STEP 03",
        "icon": "🤖",
        "title": "SARIMAX Forecast",
        "desc": "Physics-infused time-series ML models predict water levels 24 to 72 hours ahead.",
    },
    {
        "num": "STEP 04",
        "icon": "🚦",
        "title": "Risk Engine",
        "desc": "Zone-aware traffic light system classifies risk across 20 Lagos Local Government Areas.",
    },
]

for col, step in zip(steps_cols, steps):
    with col:
        st.markdown(f"""
            <div class="step-card">
                <div class="step-num">{step['num']}</div>
                <div class="step-icon">{step['icon']}</div>
                <div class="step-title">{step['title']}</div>
                <div class="step-desc">{step['desc']}</div>
            </div>
        """, unsafe_allow_html=True)

st.markdown('<div class="eco-divider"></div>', unsafe_allow_html=True)

# ── Coverage Summary ────────────────────────────────────────────────────────
st.markdown("""
    <div class="glass-card" style="text-align: center; padding: 32px 24px;">
        <div style="font-size: 13px; font-weight: 800; color: var(--primary);
                    letter-spacing: 1.2px; text-transform: uppercase; margin-bottom: 20px;">
            COVERAGE & IMPACT
        </div>
        <div style="display: flex; justify-content: center; gap: 48px; flex-wrap: wrap;">
            <div>
                <div style="font-size: 40px; font-weight: 900; color: var(--primary);">20</div>
                <div style="font-size: 14px; font-weight: 600; color: var(--text-secondary);">LGA Zones</div>
            </div>
            <div>
                <div style="font-size: 40px; font-weight: 900; color: var(--secondary);">24M+</div>
                <div style="font-size: 14px; font-weight: 600; color: var(--text-secondary);">Residents Protected</div>
            </div>
            <div>
                <div style="font-size: 40px; font-weight: 900; color: var(--accent);">72h</div>
                <div style="font-size: 14px; font-weight: 600; color: var(--text-secondary);">Forecast Horizon</div>
            </div>
            <div>
                <div style="font-size: 40px; font-weight: 900; color: var(--success);">6</div>
                <div style="font-size: 14px; font-weight: 600; color: var(--text-secondary);">Harmonic Constituents</div>
            </div>
        </div>
    </div>
""", unsafe_allow_html=True)
