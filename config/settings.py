"""
Eco-Tide Configuration & Settings
All constants, coordinates, thresholds, and zone definitions for Lagos, Nigeria.
"""

import os
from datetime import datetime

# ─── Project Paths ──────────────────────────────────────────────────────────
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")
RAW_DATA_DIR = os.path.join(DATA_DIR, "raw")
PROCESSED_DATA_DIR = os.path.join(DATA_DIR, "processed")
MODELS_DIR = os.path.join(BASE_DIR, "models", "saved")

# ─── Lagos Geographic Constants ─────────────────────────────────────────────
LAGOS_CENTER = {"lat": 6.5244, "lon": 3.3792}
LAGOS_BBOX = {"lat_min": 6.38, "lat_max": 6.70, "lon_min": 2.70, "lon_max": 4.10}

# Coordinates for Open-Meteo weather API (city center)
WEATHER_LAT = 6.52
WEATHER_LON = 3.38

# Coordinates for Open-Meteo marine API (offshore Lagos, Gulf of Guinea)
MARINE_LAT = 6.30
MARINE_LON = 3.40

# ─── Tidal Constants for Lagos ──────────────────────────────────────────────
# Lagos has a semidiurnal tidal regime
# Tidal Form Factor F = (K1 + O1) / (M2 + S2) ≈ 0.15 (semidiurnal)
TIDAL_CONSTITUENTS = {
    "M2": {"amplitude_m": 0.42, "phase_deg": 210, "period_hr": 12.4206},
    "S2": {"amplitude_m": 0.15, "phase_deg": 240, "period_hr": 12.0000},
    "K1": {"amplitude_m": 0.06, "phase_deg": 30,  "period_hr": 23.9345},
    "O1": {"amplitude_m": 0.04, "phase_deg": 350, "period_hr": 25.8193},
    "N2": {"amplitude_m": 0.09, "phase_deg": 195, "period_hr": 12.6583},
    "K2": {"amplitude_m": 0.04, "phase_deg": 250, "period_hr": 11.9672},
}
MEAN_SEA_LEVEL_M = 0.5  # Approximate MSL above chart datum for Lagos

# ─── Traffic Light Risk Thresholds ──────────────────────────────────────────
# Risk levels are zone-aware: threshold = zone_elevation_m * fraction
RISK_THRESHOLDS = {
    "green": {
        "water_level_fraction": 0.25,   # Predicted level < 25% of zone elevation
        "rainfall_mm_hr": 10,           # Light rain
        "wind_speed_ms": 8,             # Moderate wind
        "label": "Safe",
        "color": "#00C853",
        "icon": "🟢",
        "action": "Normal operations. No flood risk expected."
    },
    "amber": {
        "water_level_fraction": 0.50,   # Predicted level 25-50% of zone elevation
        "rainfall_mm_hr": 25,           # Heavy rain
        "wind_speed_ms": 15,            # Strong wind
        "label": "Caution",
        "color": "#FFD600",
        "icon": "🟡",
        "action": "Monitor conditions. Prepare for possible evacuation."
    },
    "red": {
        "water_level_fraction": 0.75,   # Predicted level > 50% of zone elevation
        "rainfall_mm_hr": 50,           # Extreme rain
        "wind_speed_ms": 25,            # Severe wind
        "label": "Danger",
        "color": "#FF1744",
        "icon": "🔴",
        "action": "EVACUATE low-lying areas. Secure property immediately."
    }
}

# Absolute thresholds (when surge exceeds these regardless of zone)
# Absolute thresholds for coastal storm surge & high sea level
# Grounded in Lagos Harbour Hydrography (LAT / Chart Datum):
# Mean Sea Level (MSL): ~0.46m | MHWS: ~0.95m | HAT: ~1.30m
# Safe Operating Tidal Envelope: < 1.40m
# Tidal Lock / Elevated Swell Advisory: 1.40m to 1.95m
# Severe Coastal Storm Surge / Overtopping Danger: >= 2.00m (user-calibrated buffer)
ABSOLUTE_SURGE_THRESHOLDS = {
    "green_max_m": 1.40,
    "amber_max_m": 1.95,
    "red_min_m": 2.00,
}

# ─── All 20 Lagos Local Government Areas ────────────────────────────────────
# Each zone has: name, lat, lon, avg_elevation_m, distance_to_water_km,
# risk_category, notable_areas, population_estimate
LAGOS_ZONES = [
    {
        "id": 1, "name": "Eti-Osa",
        "lat": 6.4294, "lon": 3.4584,
        "elevation_m": 6.0,  # Copernicus DEM (30m resolution)
        "distance_to_water_km": 0.1,
        "risk_category": "very_high",
        "notable_areas": "Victoria Island, Lekki Phase 1, Ikoyi, Banana Island",
        "drainage_capacity": 0.4,
        "population": 397_000,
        "description": "Low-lying peninsula between Lagos Lagoon and Atlantic Ocean. Contains Nigeria's financial district."
    },
    {
        "id": 2, "name": "Lagos Island",
        "lat": 6.4541, "lon": 3.3947,
        "elevation_m": 8.0,  # Copernicus DEM (30m resolution)
        "distance_to_water_km": 0.2,
        "risk_category": "high",
        "notable_areas": "Marina, Broad Street, Tinubu Square, CMS",
        "drainage_capacity": 0.3,
        "population": 860_000,
        "description": "Historic commercial center surrounded by Lagos Lagoon. Dense population with aging drainage infrastructure."
    },
    {
        "id": 3, "name": "Apapa",
        "lat": 6.4488, "lon": 3.3592,
        "elevation_m": 6.0,  # Copernicus DEM (30m resolution)
        "distance_to_water_km": 0.1,
        "risk_category": "high",
        "notable_areas": "Apapa Port, Tin Can Island, Wharf Road",
        "drainage_capacity": 0.4,
        "population": 523_000,
        "description": "Nigeria's main port district. Waterfront location on Lagos Lagoon with critical shipping infrastructure."
    },
    {
        "id": 4, "name": "Ajeromi-Ifelodun",
        "lat": 6.4476, "lon": 3.3313,
        "elevation_m": 6.0,  # Copernicus DEM (30m resolution)
        "distance_to_water_km": 0.3,
        "risk_category": "very_high",
        "notable_areas": "Ajegunle, Olodi-Apapa, Boundary",
        "drainage_capacity": 0.1,
        "population": 1_435_000,
        "description": "Densely populated waterfront community. Home to Ajegunle — one of Lagos' most flood-vulnerable informal settlements."
    },
    {
        "id": 5, "name": "Amuwo-Odofin",
        "lat": 6.4676, "lon": 3.2945,
        "elevation_m": 5.0,  # Copernicus DEM (30m resolution)
        "distance_to_water_km": 0.5,
        "risk_category": "high",
        "notable_areas": "Festac Town, Mile 2, Satellite Town",
        "drainage_capacity": 0.3,
        "population": 598_000,
        "description": "Built on reclaimed swampland and creek systems. Frequent flooding due to poor drainage and proximity to creeks."
    },
    {
        "id": 6, "name": "Badagry",
        "lat": 6.4183, "lon": 2.8814,
        "elevation_m": 4.0,  # Copernicus DEM (30m resolution)
        "distance_to_water_km": 0.5,
        "risk_category": "high",
        "notable_areas": "Badagry Beach, Gberefu Island, Seme Border",
        "drainage_capacity": 0.6,
        "population": 380_000,
        "description": "Coastal LGA on the western Lagos border. Directly exposed to Atlantic Ocean storm surges."
    },
    {
        "id": 7, "name": "Ojo",
        "lat": 6.4676, "lon": 3.1823,
        "elevation_m": 7.0,  # Copernicus DEM (30m resolution)
        "distance_to_water_km": 1.0,
        "risk_category": "moderate_high",
        "notable_areas": "Alaba International Market, LASU, Trade Fair",
        "drainage_capacity": 0.3,
        "population": 941_000,
        "description": "Creek-side LGA with low-lying areas prone to tidal flooding during spring tides."
    },
    {
        "id": 8, "name": "Lagos Mainland",
        "lat": 6.5052, "lon": 3.3633,
        "elevation_m": 7.0,  # Copernicus DEM (30m resolution)
        "distance_to_water_km": 0.3,
        "risk_category": "high",
        "notable_areas": "Makoko, Ebute-Metta, Yaba, Oyingbo",
        "drainage_capacity": 0.2,
        "population": 629_000,
        "description": "Home to Makoko — the iconic floating community on Lagos Lagoon. Extremely vulnerable to lagoon flooding."
    },
    {
        "id": 9, "name": "Surulere",
        "lat": 6.5008, "lon": 3.3485,
        "elevation_m": 7.0,  # Copernicus DEM (30m resolution)
        "distance_to_water_km": 2.0,
        "risk_category": "moderate",
        "notable_areas": "National Stadium, Adeniran Ogunsanya, Bode Thomas",
        "drainage_capacity": 0.5,
        "population": 1_274_000,
        "description": "Inland residential area but experiences pluvial flooding due to inadequate drainage channels."
    },
    {
        "id": 10, "name": "Ibeju-Lekki",
        "lat": 6.4964, "lon": 3.7571,
        "elevation_m": 1.0,  # Copernicus DEM (30m resolution)
        "distance_to_water_km": 0.5,
        "risk_category": "high",
        "notable_areas": "Dangote Refinery, Lekki Free Trade Zone, Eleko Beach",
        "drainage_capacity": 0.5,
        "population": 117_000,
        "description": "Rapidly developing coastal LGA. Low-lying terrain between Atlantic Ocean and Lekki Lagoon."
    },
    {
        "id": 11, "name": "Kosofe",
        "lat": 6.5966, "lon": 3.3896,
        "elevation_m": 10.0,  # Copernicus DEM (30m resolution)
        "distance_to_water_km": 2.0,
        "risk_category": "moderate",
        "notable_areas": "Ketu, Ojota, Mile 12, Ogudu",
        "drainage_capacity": 0.3,
        "population": 934_000,
        "description": "Adjacent to Lagos Lagoon. Moderate flood risk from lagoon overflow and poor drainage."
    },
    {
        "id": 12, "name": "Ikorodu",
        "lat": 6.6194, "lon": 3.5105,
        "elevation_m": 23.0,  # Copernicus DEM (30m resolution)
        "distance_to_water_km": 1.0,
        "risk_category": "moderate",
        "notable_areas": "Ikorodu Town, Igbogbo, Bayeku",
        "drainage_capacity": 0.4,
        "population": 689_000,
        "description": "Located on the Lagos Lagoon shore. Experiences flooding from lagoon surges and Ogun River overflow."
    },
    {
        "id": 13, "name": "Epe",
        "lat": 6.5854, "lon": 3.9792,
        "elevation_m": 24.0,  # Copernicus DEM (30m resolution)
        "distance_to_water_km": 1.5,
        "risk_category": "moderate",
        "notable_areas": "Epe Town, Lekki Lagoon, Epe Fish Market",
        "drainage_capacity": 0.5,
        "population": 323_000,
        "description": "Located on Lekki Lagoon. Semi-rural with moderate flood risk from lagoon water level changes."
    },
    {
        "id": 14, "name": "Shomolu",
        "lat": 6.5520, "lon": 3.3710,
        "elevation_m": 5.0,  # Copernicus DEM (30m resolution)
        "distance_to_water_km": 3.0,
        "risk_category": "low_moderate",
        "notable_areas": "Bariga, Gbagada, Pedro, Somolu",
        "drainage_capacity": 0.4,
        "population": 1_025_000,
        "description": "Inland residential area. Flooding mainly from blocked drainage channels during heavy rain."
    },
    {
        "id": 15, "name": "Mushin",
        "lat": 6.5381, "lon": 3.3534,
        "elevation_m": 23.0,  # Copernicus DEM (30m resolution)
        "distance_to_water_km": 4.0,
        "risk_category": "low_moderate",
        "notable_areas": "Mushin Market, Idi-Araba, Palm Avenue",
        "drainage_capacity": 0.2,
        "population": 1_321_000,
        "description": "Densely populated inland LGA. Flash flooding from overwhelmed drainage during intense rainfall."
    },
    {
        "id": 16, "name": "Oshodi-Isolo",
        "lat": 6.5353, "lon": 3.3214,
        "elevation_m": 3.0,  # Copernicus DEM (30m resolution)
        "distance_to_water_km": 4.0,
        "risk_category": "low_moderate",
        "notable_areas": "Oshodi Transport Interchange, Isolo, Ajao Estate, Airport",
        "drainage_capacity": 0.4,
        "population": 1_134_000,
        "description": "Inland LGA near Murtala Muhammed Airport. Pluvial flooding risk due to flat terrain and drainage issues."
    },
    {
        "id": 17, "name": "Ikeja",
        "lat": 6.6018, "lon": 3.3515,
        "elevation_m": 32.0,  # Copernicus DEM (30m resolution)
        "distance_to_water_km": 7.0,
        "risk_category": "low",
        "notable_areas": "Lagos State Secretariat, Allen Avenue, GRA Ikeja, Airport",
        "drainage_capacity": 0.8,
        "population": 648_000,
        "description": "Lagos State capital. Higher elevation provides natural protection from coastal flooding."
    },
    {
        "id": 18, "name": "Agege",
        "lat": 6.6199, "lon": 3.3290,
        "elevation_m": 43.0,  # Copernicus DEM (30m resolution)
        "distance_to_water_km": 9.0,
        "risk_category": "low",
        "notable_areas": "Agege Stadium, Pen Cinema, Ogba",
        "drainage_capacity": 0.6,
        "population": 1_033_000,
        "description": "Inland high-elevation LGA. Minimal coastal flood risk; localized pluvial flooding possible."
    },
    {
        "id": 19, "name": "Ifako-Ijaiye",
        "lat": 6.6477, "lon": 3.3036,
        "elevation_m": 48.0,  # Copernicus DEM (30m resolution)
        "distance_to_water_km": 10.0,
        "risk_category": "low",
        "notable_areas": "Ifako, Ijaiye, Abule Egba, LUTH",
        "drainage_capacity": 0.7,
        "population": 744_000,
        "description": "Northern Lagos LGA with highest elevation. Essentially no coastal flood risk."
    },
    {
        "id": 20, "name": "Alimosho",
        "lat": 6.6105, "lon": 3.2606,
        "elevation_m": 38.0,  # Copernicus DEM (30m resolution)
        "distance_to_water_km": 8.0,
        "risk_category": "low",
        "notable_areas": "Egbeda, Idimu, Akowonjo, Iyana Ipaja",
        "drainage_capacity": 0.6,
        "population": 2_047_000,
        "description": "Most populous LGA in Lagos. High elevation protects from coastal flooding."
    },
]

# ─── Risk Category Colors (for maps and charts) ────────────────────────────
RISK_COLORS = {
    "very_high": "#FF1744",    # Red
    "high": "#FF6D00",         # Orange
    "moderate_high": "#FFD600", # Yellow
    "moderate": "#FFAB00",     # Amber
    "low_moderate": "#76FF03", # Light Green
    "low": "#00C853",          # Green
}

RISK_LABELS = {
    "very_high": "🔴 Very High Risk",
    "high": "🟠 High Risk",
    "moderate_high": "🟡 Moderate-High Risk",
    "moderate": "🟡 Moderate Risk",
    "low_moderate": "🟢 Low-Moderate Risk",
    "low": "🟢 Low Risk",
}

# ─── Open-Meteo API Configuration ──────────────────────────────────────────
OPENMETEO_HISTORICAL_URL = "https://archive-api.open-meteo.com/v1/archive"
OPENMETEO_MARINE_URL = "https://marine-api.open-meteo.com/v1/marine"
OPENMETEO_FORECAST_URL = "https://api.open-meteo.com/v1/forecast"

# Variables to fetch from weather API
WEATHER_VARIABLES = [
    "temperature_2m",
    "relative_humidity_2m",
    "precipitation",
    "pressure_msl",
    "wind_speed_10m",
    "wind_direction_10m",
    "soil_moisture_0_to_7cm",
    "cloud_cover",
]

# Variables to fetch from marine API
MARINE_VARIABLES = [
    "wave_height",
    "wave_period",
    "wave_direction",
]

# Date range for data fetching (6+ years of data for robust model training)
DATA_START_DATE = "2020-01-01"
DATA_END_DATE = datetime.now().strftime("%Y-%m-%d")

# ─── Model Configuration ───────────────────────────────────────────────────
SARIMAX_CONFIG = {
    "seasonal_period": 24,      # 24 hours (daily cycle for residuals)
    "max_p": 3,
    "max_q": 3,
    "max_P": 1,
    "max_Q": 1,
    "information_criterion": "aic",
    "stepwise": True,
}

# Features used as exogenous variables in SARIMAX
EXOGENOUS_FEATURES = [
    "rainfall_mm",
    "pressure_hpa",
    "wind_speed_ms",
    "wind_dir_sin",      # sin(wind_direction) for circular encoding
    "wind_dir_cos",      # cos(wind_direction) for circular encoding
    "sst_celsius",
    "soil_moisture",
    "river_discharge_est",
    "wave_height_m",
    "moon_phase",
]

# ─── Dashboard Theme ───────────────────────────────────────────────────────
THEME = {
    "primary_color": "#0A84FF",
    "secondary_color": "#00C7BE",
    "accent_color": "#FF6B35",
    "bg_dark": "#0A0E27",
    "bg_card": "#131837",
    "bg_card_hover": "#1A2147",
    "text_primary": "#FFFFFF",
    "text_secondary": "#8B95B2",
    "gradient_start": "#0A84FF",
    "gradient_end": "#00C7BE",
    "danger": "#FF1744",
    "warning": "#FFD600",
    "success": "#00C853",
    "font_family": "'Inter', 'Segoe UI', sans-serif",
}

# Map tile URLs (completely free open-source, no API key required)
MAP_TILE = "https://tile.openstreetmap.org/{z}/{x}/{y}.png"
MAP_TILE_DARK = "https://tiles.stadiamaps.com/tiles/alidade_smooth_dark/{z}/{x}/{y}{r}.png"
MAP_TILE_ATTR = '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'

# Granular street-level communities database
try:
    from config.lagos_communities import LAGOS_COMMUNITY_HOTSPOTS
except Exception:
    LAGOS_COMMUNITY_HOTSPOTS = []
