"""
Eco-Tide: Geolocation Module
Captures the device's GPS location via the browser Geolocation API
using streamlit-js-eval (works on desktop Chrome/Firefox/Edge and all mobile browsers).

Usage:
    from components.geolocation import render_location_widget, get_nearest_zone, get_distance_to_zone
"""

import math
import streamlit as st
from datetime import datetime, timezone
from streamlit_js_eval import get_geolocation


# ── Haversine distance ────────────────────────────────────────────────────────
def _haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Return great-circle distance in km between two lat/lon points."""
    R = 6371.0
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlam = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlam / 2) ** 2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def get_nearest_zone(user_lat: float, user_lon: float, zones: list) -> dict | None:
    """Return the Lagos zone dict closest to (user_lat, user_lon)."""
    if not zones:
        return None
    return min(zones, key=lambda z: _haversine_km(user_lat, user_lon, z["lat"], z["lon"]))


def get_distance_to_zone(user_lat: float, user_lon: float, zone: dict) -> float:
    """Return km distance from user to a zone centroid."""
    return _haversine_km(user_lat, user_lon, zone["lat"], zone["lon"])


def render_location_widget(key_prefix: str = "location", zones: list | None = None) -> dict | None:
    """
    Render a responsive mobile-friendly GPS location control.
    Returns the user's location dict: {'lat', 'lon', 'accuracy_m', 'timestamp'} or None.
    """
    if "user_location" not in st.session_state:
        st.session_state.user_location = None
    if "user_nearest_zone" not in st.session_state:
        st.session_state.user_nearest_zone = None

    pending_key = f"{key_prefix}_location_request_pending"
    request_id_key = f"{key_prefix}_location_request_id"
    error_key = f"{key_prefix}_location_error"

    if pending_key not in st.session_state:
        st.session_state[pending_key] = False
    if request_id_key not in st.session_state:
        st.session_state[request_id_key] = 0
    if error_key not in st.session_state:
        st.session_state[error_key] = None

    col_btn, col_rst = st.columns([3, 1])
    with col_btn:
        btn_label = (
            "🔄 Re-detect GPS Location"
            if st.session_state.user_location
            else "📍 Auto-Detect My Location (GPS)"
        )
        if st.button(
            btn_label,
            type="primary",
            use_container_width=True,
            key=f"{key_prefix}_req_loc_btn",
        ):
            st.session_state[request_id_key] += 1
            st.session_state[pending_key] = True
            st.session_state[error_key] = None

    with col_rst:
        if st.session_state.user_location:
            if st.button("✖ Clear", key=f"{key_prefix}_clear_btn", use_container_width=True):
                st.session_state.user_location = None
                st.session_state.user_nearest_zone = None
                st.session_state[pending_key] = False
                st.rerun()

    # Query browser Geolocation API
    if st.session_state[pending_key]:
        result = get_geolocation(
            component_key=f"eco_tide_geo_{key_prefix}_{st.session_state[request_id_key]}"
        )
        if isinstance(result, dict):
            error = result.get("error")
            coords = result.get("coords")
            if isinstance(error, dict):
                error_messages = {
                    0: "Your browser does not support location access.",
                    1: "Location permission denied. Please allow location in your browser and tap again.",
                    2: "Position unavailable. Please try outdoors or near a window.",
                    3: "Location lookup timed out. Please try again.",
                }
                code = error.get("code")
                st.session_state[error_key] = error_messages.get(
                    code, error.get("message", "Unable to retrieve location.")
                )
                st.session_state[pending_key] = False
            elif isinstance(coords, dict):
                try:
                    lat = float(coords["latitude"])
                    lon = float(coords["longitude"])
                    accuracy = coords.get("accuracy")
                    accuracy_m = float(accuracy) if accuracy is not None else None
                    valid = (
                        math.isfinite(lat)
                        and math.isfinite(lon)
                        and -90 <= lat <= 90
                        and -180 <= lon <= 180
                    )
                except (KeyError, TypeError, ValueError):
                    valid = False

                if valid:
                    captured_at = datetime.now(timezone.utc).isoformat(timespec="seconds")
                    loc_dict = {
                        "lat": lat,
                        "lon": lon,
                        "accuracy_m": accuracy_m,
                        "timestamp": captured_at,
                    }
                    st.session_state.user_location = loc_dict
                    st.session_state[error_key] = None

                    # Automatically calculate nearest LGA
                    if zones:
                        nearest = get_nearest_zone(lat, lon, zones)
                        if nearest:
                            st.session_state.user_nearest_zone = nearest["name"]
                            st.session_state.user_location_dist_km = get_distance_to_zone(lat, lon, nearest)
                else:
                    st.session_state[error_key] = "Browser returned invalid GPS data. Please retry."
                st.session_state[pending_key] = False
                st.rerun()

    if st.session_state[pending_key]:
        st.info("📡 Requesting GPS from your device... please tap 'Allow' if prompted by your browser.")
    elif st.session_state[error_key]:
        st.warning(f"⚠️ {st.session_state[error_key]}")

    # Display active GPS badge if captured
    user_loc = st.session_state.user_location
    if user_loc:
        acc_str = f" • ±{user_loc['accuracy_m']:.0f}m" if user_loc.get("accuracy_m") else ""
        nearest_str = f" • Nearest LGA: <b>{st.session_state.get('user_nearest_zone', '')}</b>" if st.session_state.get('user_nearest_zone') else ""
        st.markdown(
            f"""<div style="background:rgba(16,185,129,0.12); border:1px solid #10B981; border-radius:10px;
                        padding:10px 14px; font-size:0.86rem; color:var(--text-primary); margin:8px 0;">
                🟢 <b>GPS Locked:</b> {user_loc['lat']:.4f}°N, {user_loc['lon']:.4f}°E{acc_str}{nearest_str}
            </div>""",
            unsafe_allow_html=True
        )

    return st.session_state.user_location


def render_location_card(zone_risks: list, zones: list, theme: str = "dark") -> dict | None:
    """Wrapper for backward compatibility."""
    return render_location_widget(key_prefix="community", zones=zones)
