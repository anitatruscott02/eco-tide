"""
Eco-Tide: Live Forecast Fetcher
Fetches live weather and marine forecast from Open-Meteo APIs.
"""

import os
import sys
import requests
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import warnings

# Force UTF-8 encoding for standard output to fix Windows console crashes with emojis
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

warnings.filterwarnings("ignore")

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config.settings import (
    WEATHER_LAT, WEATHER_LON, MARINE_LAT, MARINE_LON,
    OPENMETEO_FORECAST_URL, OPENMETEO_MARINE_URL,
    PROCESSED_DATA_DIR, TIDAL_CONSTITUENTS, MEAN_SEA_LEVEL_M,
)

def fetch_weather_forecast():
    print(f"📡 Fetching live weather forecast for Lagos ({WEATHER_LAT}°N, {WEATHER_LON}°E)...")
    variables = [
        "temperature_2m", "relative_humidity_2m", "precipitation",
        "pressure_msl", "wind_speed_10m", "wind_direction_10m",
        "soil_moisture_0_to_7cm", "cloud_cover"
    ]
    params = {
        "latitude": WEATHER_LAT,
        "longitude": WEATHER_LON,
        "hourly": ",".join(variables),
        "timezone": "Africa/Lagos",
    }
    
    response = requests.get(OPENMETEO_FORECAST_URL, params=params, timeout=120)
    response.raise_for_status()
    data = response.json()
    
    hourly = data["hourly"]
    df = pd.DataFrame({
        "datetime": pd.to_datetime(hourly["time"]),
        "temperature_celsius": hourly["temperature_2m"],
        "relative_humidity_2m": hourly["relative_humidity_2m"],
        "rainfall_mm": hourly["precipitation"],
        "pressure_hpa": hourly["pressure_msl"],
        "wind_speed_ms": hourly["wind_speed_10m"],
        "wind_direction_deg": hourly["wind_direction_10m"],
        "soil_moisture": hourly["soil_moisture_0_to_7cm"],
        "cloud_cover": hourly["cloud_cover"],
    })
    df.set_index("datetime", inplace=True)
    print(f"   ✅ Fetched {len(df)} weather forecast records")
    return df


def fetch_marine_forecast():
    print(f"🌊 Fetching live marine forecast offshore Lagos ({MARINE_LAT}°N, {MARINE_LON}°E)...")
    variables = ["wave_height", "wave_period", "wave_direction"]
    params = {
        "latitude": MARINE_LAT,
        "longitude": MARINE_LON,
        "hourly": ",".join(variables),
        "timezone": "Africa/Lagos",
    }
    
    response = requests.get(OPENMETEO_MARINE_URL, params=params, timeout=120)
    response.raise_for_status()
    data = response.json()
    
    hourly = data["hourly"]
    df = pd.DataFrame({
        "datetime": pd.to_datetime(hourly["time"]),
        "wave_height_m": hourly["wave_height"],
        "wave_period_s": hourly["wave_period"],
        "wave_direction_deg_marine": hourly["wave_direction"],
    })
    df.set_index("datetime", inplace=True)
    print(f"   ✅ Fetched {len(df)} marine forecast records")
    return df


def compute_moon_phases(dates):
    """Simplified moon phase using synodic period (29.53 days)"""
    SYNODIC_PERIOD = 29.53059  # days
    # Known new moon reference: Jan 6, 2000 at 18:14 UTC
    REF_NEW_MOON = datetime(2000, 1, 6, 18, 14)

    phases = []
    for dt in dates:
        days_since_ref = (dt.to_pydatetime() - REF_NEW_MOON).total_seconds() / 86400.0
        phase = (days_since_ref % SYNODIC_PERIOD) / SYNODIC_PERIOD
        phases.append(phase)
        
    return phases


def generate_tidal_signal(dates):
    hours = np.arange(len(dates), dtype=float)
    water_level = np.full(len(dates), MEAN_SEA_LEVEL_M)

    for name, params in TIDAL_CONSTITUENTS.items():
        amp = params["amplitude_m"]
        phase = np.radians(params["phase_deg"])
        period = params["period_hr"]
        angular_freq = 2 * np.pi / period
        water_level += amp * np.cos(angular_freq * hours - phase)
        
    return water_level

def main():
    print("=" * 70)
    print("🌅 ECO-TIDE DATA PIPELINE — Fetching Live Forecast")
    print("=" * 70)
    
    os.makedirs(PROCESSED_DATA_DIR, exist_ok=True)
    
    weather_df = fetch_weather_forecast()
    marine_df = fetch_marine_forecast()
    
    merged_df = weather_df.join(marine_df, how="inner")
    
    merged_df["moon_phase"] = compute_moon_phases(merged_df.index)
    merged_df["tidal_water_level_m"] = generate_tidal_signal(merged_df.index)
    
    out_path = os.path.join(PROCESSED_DATA_DIR, "live_forecast.csv")
    merged_df.to_csv(out_path)
    
    print(f"   ✅ Saved live forecast dataset: {len(merged_df)} records")
    print("=" * 70)
    return merged_df

if __name__ == "__main__":
    main()
