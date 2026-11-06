import streamlit as st
import sys, os

if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.settings import THEME
from utils.theme import init_theme, render_theme_switcher, inject_theme_css

# ── Dynamic Theme & Sidebar Switcher ────────────────────────────────────────
init_theme()
inject_theme_css()

with st.sidebar:
    render_theme_switcher()

# ── Page Configuration & CSS Injection ────────────────────────────────────────
METHODOLOGY_CSS = """
<style>
/* ── Hero Banner ──────────────────────────────────────── */
.meth-hero {
    background: linear-gradient(135deg, rgba(14, 165, 233, 0.15) 0%, rgba(20, 184, 166, 0.15) 50%, rgba(99, 102, 241, 0.15) 100%);
    border: 1px solid rgba(56, 189, 248, 0.3);
    border-radius: 20px;
    padding: 36px 32px;
    text-align: center;
    margin-bottom: 28px;
    box-shadow: 0 12px 32px rgba(0, 0, 0, 0.25);
    backdrop-filter: blur(12px);
}
.meth-badge {
    display: inline-block;
    background: rgba(56, 189, 248, 0.15);
    border: 1px solid rgba(56, 189, 248, 0.3);
    color: #38BDF8;
    font-size: 0.78rem;
    font-weight: 700;
    letter-spacing: 1.5px;
    text-transform: uppercase;
    padding: 6px 16px;
    border-radius: 20px;
    margin-bottom: 12px;
}
.meth-title {
    font-size: 2.4rem;
    font-weight: 900;
    background: linear-gradient(135deg, #38BDF8, #2DD4BF, #818CF8);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    margin-bottom: 10px;
    line-height: 1.2;
}
.meth-subtitle {
    font-size: 1.05rem;
    color: var(--text-secondary);
    max-width: 720px;
    margin: 0 auto;
    line-height: 1.6;
    font-weight: 500;
}

/* ── Section Cards ────────────────────────────────────── */
.meth-card {
    background: var(--bg-card) !important;
    border: 1px solid var(--border-card) !important;
    border-radius: 18px;
    padding: 28px 30px;
    margin-bottom: 22px;
    box-shadow: var(--shadow-card) !important;
    backdrop-filter: blur(16px);
    transition: transform 0.25s ease, border-color 0.25s ease, box-shadow 0.25s ease;
    color: var(--text-body) !important;
}
.meth-card:hover {
    transform: translateY(-3px);
    border-color: var(--primary) !important;
    box-shadow: var(--shadow-card-hover) !important;
}
.meth-card-header {
    display: flex;
    align-items: center;
    gap: 14px;
    margin-bottom: 16px;
    padding-bottom: 14px;
    border-bottom: 1px solid var(--border-card) !important;
}
.meth-card-icon {
    font-size: 1.8rem;
    background: rgba(2, 132, 199, 0.1);
    width: 48px;
    height: 48px;
    display: flex;
    align-items: center;
    justify-content: center;
    border-radius: 12px;
    border: 1px solid var(--border-card);
}
.meth-card-title {
    font-size: 1.35rem;
    font-weight: 800;
    color: var(--text-primary) !important;
    margin: 0;
}
.meth-card p, .meth-card li, .meth-card span {
    color: var(--text-secondary) !important;
    font-size: 0.98rem;
    line-height: 1.7;
}
.meth-card strong {
    color: var(--text-primary) !important;
}
.meth-highlight {
    color: var(--primary) !important;
    font-weight: 700;
}
.meth-pill-grid {
    display: flex;
    gap: 12px;
    flex-wrap: wrap;
    margin: 16px 0;
}
.meth-pill {
    background: var(--bg-card-subtle) !important;
    border: 1px solid var(--border-card) !important;
    border-radius: 10px;
    padding: 10px 16px;
    font-size: 0.88rem;
    color: var(--text-primary) !important;
}
.meth-pill b {
    color: var(--primary) !important;
}
</style>
"""
st.markdown(METHODOLOGY_CSS, unsafe_allow_html=True)

# ── Hero Banner ───────────────────────────────────────────────────────────────
st.markdown("""
<div class="meth-hero">
    <div class="meth-badge">🔬 Software-First GeoAI Architecture</div>
    <div class="meth-title">The Science & Engineering Behind Eco-Tide</div>
    <div class="meth-subtitle">
        How we combine satellite Earth Observation, 6-constituent tidal harmonics, 
        SARIMAX machine learning, and zone-aware physics to protect 24 million Lagosians.
    </div>
</div>
""", unsafe_allow_html=True)

# ── 1. Software-First GeoAI ───────────────────────────────────────────────────
st.markdown("""
<div class="meth-card" style="border-left: 5px solid #38BDF8;">
    <div class="meth-card-header">
        <div class="meth-card-icon">🛰️</div>
        <div class="meth-card-title">1. Software-First GeoAI Philosophy</div>
    </div>
    <p>
        Traditional flood early warning systems rely on physical tide gauges and local weather station hardware. 
        In coastal megacities like Lagos, historical infrastructure (such as NIWA gauges) frequently suffers from power outages, 
        maintenance blackouts, or sensor vandalism, leaving millions in the dark when storm surges hit.
    </p>
    <p>
        <strong>Eco-Tide takes a radically different approach: 100% Software-First GeoAI.</strong> 
        By bypassing physical hardware dependencies, we stream continuous high-resolution satellite data and meteorological APIs directly from orbit:
    </p>
    <ul>
        <li><strong class="meth-highlight">Open-Meteo & ECMWF:</strong> Real-time atmospheric pressure, rainfall intensity, wind vectors, and marine wave dynamics.</li>
        <li><strong class="meth-highlight">Copernicus DEM (30m):</strong> European Space Agency satellite digital elevation model covering all 20 Lagos LGAs.</li>
        <li><strong class="meth-highlight">UHSLC Global Tide Registry:</strong> Satellite-calibrated tide gauge data for harmonic Constituent decomposition.</li>
    </ul>
    <p>This guarantees <strong>99.9% operational uptime</strong> and zero reliance on local hardware maintenance.</p>
</div>
""", unsafe_allow_html=True)

# ── 2. The Dataset ────────────────────────────────────────────────────────────
st.markdown("""
<div class="meth-card" style="border-left: 5px solid #2DD4BF;">
    <div class="meth-card-header">
        <div class="meth-card-icon">📊</div>
        <div class="meth-card-title">2. Multi-Variate Lagos Lagoon Dataset</div>
    </div>
    <p>
        Our forecasting models are trained on an extensive, custom-curated dataset capturing 
        the complex hydrodynamics of the Gulf of Guinea and Lagos Lagoon basin:
    </p>
    <div class="meth-pill-grid">
        <div class="meth-pill">📅 <b>5+ Years</b> Continuous Data (2020–Present)</div>
        <div class="meth-pill">📈 <b>43,000+</b> Hourly Records</div>
        <div class="meth-pill">🔬 <b>35</b> Environmental Features per Record</div>
    </div>
    <p>
        Features include M2/S2/K1/O1/N2/K2 tidal constituents, moon phases, offshore wave heights, 
        wind vector decomposition (sin/cos angles), sea surface temperature, atmospheric pressure, and soil moisture saturation.
    </p>
</div>
""", unsafe_allow_html=True)

# ── 3. SARIMAX AI Engine ──────────────────────────────────────────────────────
st.markdown("""
<div class="meth-card" style="border-left: 5px solid #818CF8;">
    <div class="meth-card-header">
        <div class="meth-card-icon">🧠</div>
        <div class="meth-card-title">3. SARIMAX AI Time-Series Prediction Engine</div>
    </div>
    <p>
        Predicting coastal flooding requires modeling both deterministic astronomical tides and chaotic weather-driven storm surges. 
        Eco-Tide utilizes a <strong>SARIMAX</strong> (Seasonal Auto-Regressive Integrated Moving Average with eXogenous variables) model:
    </p>
    <ul>
        <li><strong class="meth-highlight">Astronomical Harmonic Base:</strong> Decomposes 6 major constituent frequencies (M2, S2, K1, O1, N2, K2) to model deterministic lunar-solar tides.</li>
        <li><strong class="meth-highlight">Exogenous Weather Matrix (X):</strong> Integrates wind speed, direction, pressure drop, rainfall, and wave setup to compute meteorological surge.</li>
        <li><strong class="meth-highlight">Residual Cycle Learning (24h):</strong> Learns diurnal lag patterns to eliminate systematic forecast drift.</li>
    </ul>
    <p>This delivers high-confidence forecasts up to <span class="meth-highlight">72 hours in advance</span>, enabling proactive emergency deployment.</p>
</div>
""", unsafe_allow_html=True)

# ── 4. Physics Engine & Compound Risk ────────────────────────────────────────
st.markdown("""
<div class="meth-card" style="border-left: 5px solid #F43F5E;">
    <div class="meth-card-header">
        <div class="meth-card-icon">🌊</div>
        <div class="meth-card-title">4. Zone-Aware Physics Engine & Compound Risk</div>
    </div>
    <p>
        Predicted water level alone is incomplete without land interaction physics. Eco-Tide evaluates 
        compound flood risk for each of the 20 Local Government Areas (LGAs) by solving:
    </p>
    <ul>
        <li><strong class="meth-highlight">Elevation Hydrodynamics (Z):</strong> Evaluated against Copernicus DEM elevations (e.g., Ibeju-Lekki is 1.0m vs Agege at 43.0m).</li>
        <li><strong class="meth-highlight">Soil Moisture Runoff Multiplier:</strong> Saturated ground (moisture > 0.8) amplifies surface runoff coefficient up to 1.0x.</li>
        <li><strong class="meth-highlight">Zuider Zee Wind Setup & Inverse Barometer:</strong> Computes coastal water stack-up from wind shear and pressure drops (1 hPa = ~1cm surge).</li>
        <li><strong class="meth-highlight">Compound Multiplier:</strong> When 3+ environmental stressors cross threshold simultaneously, risk score amplifies non-linearly.</li>
    </ul>
    <p>This triggers zone-specific traffic light alerts (🟢 Green, 🟡 Amber, 🔴 Red) with precise evacuation routing.</p>
</div>
""", unsafe_allow_html=True)

st.markdown("""
<div style="text-align: center; color: var(--text-muted); font-size: 0.85rem; padding: 20px 0;">
    Eco-Tide Coastal Flood Early Warning System • Powered by GeoAI & Copernicus Space Data
</div>
""", unsafe_allow_html=True)
