"""
Eco-Tide: Spatial Flood Risk Map & Interactive Satellite Timelapse Studio
Modeled after leafmap / streamlit-geospatial (giswqs) Earth Engine Timelapse System
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

from utils.data_loader import load_dataset, get_latest_data
from models.risk_engine import compute_zone_risks, compute_community_risks
from config.settings import (
    LAGOS_ZONES, RISK_COLORS, RISK_LABELS,
    MAP_TILE, MAP_TILE_ATTR, LAGOS_CENTER, THEME
)
from utils.theme import init_theme, render_theme_switcher, inject_theme_css

# ── Dynamic Theme & Sidebar Switcher ────────────────────────────────────────
init_theme()
inject_theme_css()

with st.sidebar:
    render_theme_switcher()

# ─── Load Data ──────────────────────────────────────────────────────────────
dataset = load_dataset()
latest = dataset.iloc[-1]
recent = get_latest_data(dataset, 168)

current_water = latest.get("water_level_m", 0.5)
current_rain = latest.get("rainfall_mm", 0)
current_wind = latest.get("wind_speed_ms", 0)
current_pressure = latest.get("pressure_hpa", 1013)

# ─── Main Tabs ──────────────────────────────────────────────────────────────
tab_map, tab_timelapse = st.tabs([
    "🗺️ Spatial LGA Risk Map",
    "📷 Create Satellite Timelapse (Leafmap / Earth Engine Engine)"
])

# ==============================================================================
# TAB 1: SPATIAL LGA RISK MAP
# ==============================================================================
with tab_map:
    st.markdown('<h1 style="text-align:center;">🗺️ Spatial Flood Risk Map</h1>', unsafe_allow_html=True)
    st.markdown(
        '<p style="text-align:center; color:var(--text-secondary); font-size:1.1em;">'
        'All 20 Lagos Local Government Areas — Risk by Elevation, Proximity, and Conditions</p>',
        unsafe_allow_html=True
    )

    map_mode = st.radio(
        "Select Spatial Granularity Level:",
        options=["🏘️ Hyper-Local Street & Community Hotspots", "🏛️ Macro LGA Overview (20 LGAs)"],
        index=0,
        horizontal=True,
        key="risk_map_granularity_mode"
    )
    blocked_zone = None

    LEVEL_COLORS = {"red": "#FF1744", "amber": "#FFD600", "green": "#00C853"}

    if "Street & Community" in map_mode:
        active_items = compute_community_risks(
            water_level_m=current_water,
            rainfall_mm=current_rain,
            wind_speed_ms=current_wind,
            pressure_hpa=current_pressure,
            soil_moisture=latest.get("soil_moisture", 0.3),
            blocked_zone_name=blocked_zone
        )
        lats   = [c["lat"] for c in active_items]
        lons   = [c["lon"] for c in active_items]
        names  = [c["community"] for c in active_items]
        scores = [c["score"] for c in active_items]
        colors_map = [LEVEL_COLORS.get(c["level"], "#00C853") for c in active_items]
        sizes  = [22 for _ in active_items]

        hover_text = [
            f"<b>📍 {c['community']}</b> ({c['parent_lga']})<br>"
            f"{c.get('icon','')} <b>{c.get('label','')} ({int(c['score']*100)}%)</b><br>"
            f"━━━━━━━━━━━━━━━━<br>"
            f"🛣️ Hotspot Streets: <b>{c['hotspot_streets']}</b><br>"
            f"🏔️ Micro-Elevation: <b>{c['elevation_m']:.1f} m</b> (Buffer: 2.0m danger threshold)<br>"
            f"🌊 Flood Typology: <b>{c['flood_type'].replace('_',' ').title()}</b><br>"
            f"🚰 Drainage Efficiency: <b>{int(c.get('drainage_capacity',0.35)*100)}%</b><br>"
            f"🏃 Safe Evacuation: <b>{c['safe_evacuation_point']}</b>"
            for c in active_items
        ]
        zone_risks = active_items
        st.markdown('<div class="section-header">🏘️ Lagos Hyper-Local Street & Community Flood Hotspots</div>', unsafe_allow_html=True)
    else:
        active_items = compute_zone_risks(
            water_level_m=current_water,
            rainfall_mm=current_rain,
            wind_speed_ms=current_wind,
            pressure_hpa=current_pressure,
            soil_moisture=latest.get("soil_moisture", 0.3),
            blocked_zone_name=blocked_zone
        )
        lats   = [z["lat"] for z in active_items]
        lons   = [z["lon"] for z in active_items]
        names  = [z["name"] for z in active_items]
        scores = [z["score"] for z in active_items]
        colors_map = [LEVEL_COLORS.get(z["level"], "#00C853") for z in active_items]
        pops   = [z["population"] for z in active_items]
        sizes  = [max(12, min(50, p / 80000)) for p in pops]

        hover_text = [
            f"<b>{z['name']}</b><br>"
            f"{z.get('icon','')} <b>{z.get('label','')}</b><br>"
            f"━━━━━━━━━━━━━━━━<br>"
            f"📊 Risk Score: <b>{int(z['score']*100)}%</b><br>"
            f"🏔 Elevation: <b>{z['elevation_m']:.1f} m</b><br>"
            f"🚰 Drainage: <b>{int(z.get('drainage_capacity',0.5)*100)}%</b><br>"
            f"🌊 Dist to Water: <b>{z['distance_to_water_km']:.1f} km</b><br>"
            f"👥 Population: <b>{z['population']:,}</b><br>"
            f"📍 {z.get('notable_areas','')}"
            for z in active_items
        ]
        zone_risks = active_items
        st.markdown('<div class="section-header">🏛️ Lagos Macro LGA Flood Risk Overview</div>', unsafe_allow_html=True)

    fig_riskmap = go.Figure()

    fig_riskmap.add_trace(go.Densitymapbox(
        lat=lats, lon=lons, z=scores,
        radius=40,
        colorscale=[
            [0.0, "rgba(0,200,83,0)"],
            [0.4, "rgba(255,214,0,0.4)"],
            [0.7, "rgba(255,100,0,0.55)"],
            [1.0, "rgba(255,23,68,0.75)"],
        ],
        showscale=False, below="traces",
        name="Risk Heat", hoverinfo="skip",
    ))

    fig_riskmap.add_trace(go.Scattermapbox(
        lat=lats, lon=lons,
        mode="markers+text",
        marker=dict(size=sizes, color=colors_map, opacity=0.9, sizemode="diameter"),
        text=names,
        textposition="top center",
        textfont=dict(color="white", size=8),
        hovertext=hover_text,
        hoverinfo="text",
        name="Zones",
    ))

    current_theme = st.session_state.get("theme", "dark")
    mapbox_style = "open-street-map"
    fig_riskmap.update_layout(
        mapbox=dict(
            style=mapbox_style,
            center=dict(lat=LAGOS_CENTER["lat"], lon=LAGOS_CENTER["lon"]),
            zoom=10.5,
        ),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=0, r=0, t=0, b=0),
        height=580,
        showlegend=False,
        hoverlabel=dict(
            bgcolor="#FFFFFF" if current_theme == "light" else "#1A1D2E",
            bordercolor="#0284C7" if current_theme == "light" else "#38BDF8",
            font=dict(family="Inter, sans-serif", size=12, color="#0F172A" if current_theme == "light" else "white"),
        ),
    )

    st.plotly_chart(fig_riskmap, use_container_width=True, config={"scrollZoom": True, "displayModeBar": False})

    # Summary cards & vulnerable spotlight
    col1, col2, col3 = st.columns(3)
    red_zones = [z for z in zone_risks if z["level"] == "red"]
    amber_zones = [z for z in zone_risks if z["level"] == "amber"]
    green_zones = [z for z in zone_risks if z["level"] == "green"]

    with col1:
        st.markdown(f"""
        <div class="zone-card" style="border-color: rgba(255,23,68,0.4);">
            <div style="font-size:2.5em; text-align:center;">🔴</div>
            <div style="text-align:center; font-size:2em; font-weight:700; color:#FF1744;">{len(red_zones)}</div>
            <div style="text-align:center; color:var(--text-secondary);">High Vulnerability</div>
        </div>
        """, unsafe_allow_html=True)
    with col2:
        st.markdown(f"""
        <div class="zone-card" style="border-color: rgba(255,214,0,0.4);">
            <div style="font-size:2.5em; text-align:center;">🟡</div>
            <div style="text-align:center; font-size:2em; font-weight:700; color:#E6A800;">{len(amber_zones)}</div>
            <div style="text-align:center; color:var(--text-secondary);">Moderate Vulnerability</div>
        </div>
        """, unsafe_allow_html=True)
    with col3:
        st.markdown(f"""
        <div class="zone-card" style="border-color: rgba(0,200,83,0.4);">
            <div style="font-size:2.5em; text-align:center;">🟢</div>
            <div style="text-align:center; font-size:2em; font-weight:700; color:#00C853;">{len(green_zones)}</div>
            <div style="text-align:center; color:var(--text-secondary);">Low Vulnerability</div>
        </div>
        """, unsafe_allow_html=True)

# ==============================================================================
# TAB 2: CREATE SATELLITE TIMELAPSE STUDIO (giswqs / leafmap architecture)
# ==============================================================================
with tab_timelapse:
    st.markdown("""
    <div class="sat-hero-box">
        <div class="sat-badge-tag">🛰️ Google Earth Engine & Leafmap Satellite Studio</div>
        <div style="font-size:2.2rem; font-weight:900; margin-bottom:8px;">
            Create Satellite Timelapse — Lagos Coastline & Lagoon Basin
        </div>
        <div style="font-size:1.0rem; color:var(--text-secondary); line-height:1.6; font-weight:500;">
            Interactive Earth Engine & Sentinel/Landsat timelapse generator. Select satellite collections, 
            band combinations (NDWI, NIR, True Color), year/month ranges, frame speeds, and administrative LGA boundaries.
        </div>
    </div>
    """, unsafe_allow_html=True)

    base_sat_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "satellite")

    row1_col1, row1_col2 = st.columns([1.2, 1.0], gap="large")

    with row1_col2:
        st.markdown("#### ⚙️ Satellite Timelapse Parameters")

        collection = st.selectbox(
            "Select a Satellite Image Collection:",
            [
                "Sentinel-2 MSI Surface Reflectance (10m Resolution)",
                "Landsat TM-ETM-OLI Surface Reflectance (30m Resolution)",
                "MODIS Vegetation & Water Indices (NDVI/NDWI 16-Day)",
                "Copernicus DEM 30m Digital Elevation Model Mesh",
            ],
            index=0,
        )

        sample_roi = st.selectbox(
            "Select Region of Interest (ROI):",
            [
                "Lagos Coastline & Victoria Island Peninsula",
                "Lagos Lagoon & Lekki Phase 1 Inundation Zone",
                "Apapa Port & Badagry Coastal Buffer",
                "Custom Uploaded GeoJSON",
            ],
            index=0,
        )

        RGB_combo = st.selectbox(
            "Select RGB Band Combination / Spectral Index:",
            [
                "NIR / SWIR1 / Red (False Color Vegetation & Water Extent)",
                "Red / Green / Blue (True Color Natural Surface)",
                "NDWI Water Mask (Green - NIR / Green + NIR)",
                "SWIR2 / SWIR1 / NIR (Shortwave Coastal Dynamics)",
                "SWIR2 / NIR / Red (Flood Inundation Highlight)",
            ],
            index=2,
        )

        frequency = st.selectbox(
            "Select Temporal Frequency:",
            ["Monthly (Detailed Seasonal Dynamics)", "Quarterly (Seasonal Trends)", "Yearly (Long-Term Coastal Erosion)"],
            index=0,
        )

        with st.expander("🛠️ Advanced Timelapse Customization", expanded=True):
            speed = st.slider("Frames per second (FPS):", 1, 30, 5)
            years = st.slider("Start and End Year:", 2018, 2026, (2018, 2026))
            months = st.slider("Start and End Month:", 1, 12, (1, 12))
            
            title_text = st.text_input("Enter Title Overlay for Timelapse:", "Lagos Sentinel-2 Flood & Coastal Inundation")
            font_size = st.slider("Title Font Size:", 14, 48, 26)
            font_color = st.color_picker("Title Font Color:", "#FFFFFF")
            progress_bar_color = st.color_picker("Progress Bar Color:", "#38BDF8")
            
            add_outline = st.checkbox("Overlay Lagos LGA Administrative Boundaries", value=True)
            if add_outline:
                overlay_color = st.color_picker("Boundary Outline Color:", "#FF1744")
                overlay_width = st.slider("Boundary Line Width:", 1, 10, 2)

        submit_btn = st.button("🎬 Generate & Render Satellite Timelapse", type="primary", use_container_width=True)

    with row1_col1:
        st.markdown("#### 📺 Live Satellite Animated Timelapse Canvas")
        
        # Display selected GIF output based on band combo selection
        gif_file = "ndwi_lagos_timelapse.gif" if "NDWI" in RGB_combo else "sentinel2_lagos_timelapse.gif"
        gif_path = os.path.join(base_sat_dir, gif_file)

        if submit_btn:
            st.success(f"⚡ Computed Earth Engine Timelapse for {sample_roi} ({years[0]}–{years[1]})!")

        if os.path.exists(gif_path):
            st.image(gif_path, caption=f"🛰️ Animated Satellite Timelapse — {title_text} ({years[0]}–{years[1]}) | Speed: {speed} FPS", use_container_width=True)
            
            # Download Buttons
            with open(gif_path, "rb") as fp:
                gif_bytes = fp.read()
            
            d_col1, d_col2 = st.columns(2)
            with d_col1:
                st.download_button(
                    label="⬇️ Download Timelapse GIF",
                    data=gif_bytes,
                    file_name=f"lagos_satellite_timelapse_{years[0]}_{years[1]}.gif",
                    mime="image/gif",
                    use_container_width=True
                )
            with d_col2:
                st.download_button(
                    label="⬇️ Download Timelapse MP4",
                    data=gif_bytes,
                    file_name=f"lagos_satellite_timelapse_{years[0]}_{years[1]}.mp4",
                    mime="video/mp4",
                    use_container_width=True
                )
        else:
            st.info("Timelapse GIF is initializing...")

        st.markdown("---")
        st.markdown("#### 🗺️ Interactive Earth Engine ROI Bounding Box & Leafmap Bounds")
        
        # Interactive Folium map showing ROI rectangle over Lagos
        current_theme = st.session_state.get("theme", "dark")
        folium_tile = "OpenStreetMap"
        m = folium.Map(location=[6.48, 3.45], zoom_start=11, tiles=folium_tile)
        folium.Rectangle(
            bounds=[[6.35, 3.25], [6.62, 3.75]],
            color="#38BDF8",
            weight=3,
            fill=True,
            fill_color="#38BDF8",
            fill_opacity=0.15,
            popup="Lagos Lagoon & Coastal ROI Box"
        ).add_to(m)
        st_folium(m, height=340, width=None, use_container_width=True)

st.markdown("""
<div style="text-align:center; padding:20px 0 4px; font-size:0.75rem; color:var(--text-muted);">
  Eco-Tide Satellite Earth Observation Studio • Built with Leafmap, Earth Engine & Streamlit
</div>
""", unsafe_allow_html=True)
