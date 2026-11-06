"""
Eco-Tide: Physics-Based Risk Engine & Community Flood Hotspots
Provides both macro LGA risk evaluation (20 LGAs) and granular street/community
flood risk analysis across 45+ monitored hotspots in Lagos.

Calibrated against Lagos Harbour hydrography (LAT / Chart Datum):
  - Mean Sea Level (MSL): ~0.46m
  - Mean High Water Springs (MHWS): ~0.95m
  - Highest Astronomical Tide (HAT): ~1.30m
  - Safe Operating Tidal Envelope: < 1.40m
  - Elevated Swell / Tidal Lock Advisory: 1.40m to 1.95m
  - Extreme Storm Surge Danger: >= 2.00m
"""

import numpy as np
import pandas as pd
from config.settings import (
    LAGOS_ZONES, RISK_THRESHOLDS, ABSOLUTE_SURGE_THRESHOLDS, RISK_COLORS, RISK_LABELS
)
try:
    from config.lagos_communities import LAGOS_COMMUNITY_HOTSPOTS
except Exception:
    LAGOS_COMMUNITY_HOTSPOTS = []


def calc_wind_setup(wind_speed_ms: float, distance_to_water_km: float) -> float:
    """
    Compute wind setup (storm surge component) using calibrated Zuiderzee formula.
    S = (U^2 * F) / (3.6e6 * d) in metric units (meters).
    """
    fetch_m = min(12000.0, max(500.0, 4000.0 / max(distance_to_water_km, 0.1)))
    depth_m = 2.5 if distance_to_water_km < 1.0 else 8.0
    setup_m = (wind_speed_ms**2 * fetch_m) / (3.6e6 * depth_m)
    return round(float(setup_m), 4)


def classify_risk_level(water_level_m, rainfall_mm=0, wind_speed_ms=0,
                        pressure_hpa=1013, zone_elevation_m=5.0, 
                        zone_drainage_capacity=0.5, soil_moisture=0.3, distance_to_water_km=1.0,
                        critical_threshold_m=2.00):
    """
    Classify flood risk using a physically grounded Traffic Light system.

    Evaluates:
    1. Coastal surge & overtopping relative to elevation buffer
    2. Pluvial flash flood risk (rainfall vs drainage capacity)
    3. Inverse barometer pressure anomaly
    4. Wind setup
    5. Soil moisture saturation & runoff coefficient

    Args:
        water_level_m: predicted total water level (meters, relative to LAT/CD)
        rainfall_mm: current rainfall rate (mm/hr)
        wind_speed_ms: wind speed (m/s)
        pressure_hpa: sea level pressure (hPa)
        zone_elevation_m: ground elevation (meters)
        zone_drainage_capacity: drainage efficiency (0.0 to 1.0)
        soil_moisture: current soil saturation level (0.0 to 1.0)
        distance_to_water_km: distance to nearest major water body (km)
        critical_threshold_m: safety surge buffer threshold (default 2.00m)

    Returns:
        dict with risk level, score, factor_scores, and recommended action
    """
    # 1. Inverse Barometer Effect (1 hPa drop below standard 1013.25 = ~1cm rise)
    ibe_m = max(0.0, (1013.25 - pressure_hpa) * 0.01)

    # 2. Wind Setup (Storm Surge)
    wind_setup_m = calc_wind_setup(wind_speed_ms, distance_to_water_km)

    effective_water_level_m = round(float(water_level_m + ibe_m + wind_setup_m), 3)

    # 3. Factor Scores Calculation (0.0 to 1.0)
    scores = []

    # Factor A: Coastal Water Level & Surge Buffer (weight: 30%)
    # In Lagos, water level < 1.40m is standard astronomical tidal range (completely safe)
    safe_tidal_ceiling = 1.40
    freeboard_buffer = 0.40  # 40cm freeboard before surface inundation

    if effective_water_level_m <= safe_tidal_ceiling:
        water_score = 0.0
    else:
        # Surge scaling between 1.40m and 2.20m
        surge_excess = (effective_water_level_m - safe_tidal_ceiling) / max(0.5, (critical_threshold_m - safe_tidal_ceiling))
        # Elevation vulnerability dampener: High elevation zones cannot be overtopped by low surges
        elevation_gap = max(0.0, (zone_elevation_m - freeboard_buffer) - effective_water_level_m)
        vulnerability_scale = 1.0 if elevation_gap <= 0.0 else max(0.0, 1.0 - (elevation_gap / 2.0))
        water_score = min(1.0, max(0.0, surge_excess * vulnerability_scale))
    scores.append(("Water Level", water_score, 0.30))

    # Factor B: Pluvial Flash Flood Risk (weight: 30%)
    # Runoff coefficient ranges from 0.2 (dry soil) to 1.0 (saturated soil)
    runoff_coefficient = 0.2 + 0.8 * min(1.0, max(0.0, soil_moisture))
    effective_drainage = max(zone_drainage_capacity, 0.10)
    # 50 mm/hr tropical rain with 50% drainage capacity = 1.0 (severe street flooding)
    pluvial_score = min(1.0, max(0.0, (rainfall_mm * runoff_coefficient) / (50.0 * effective_drainage)))
    scores.append(("Pluvial Risk", pluvial_score, 0.30))

    # Factor C: Wind Severity (weight: 15%)
    # Winds under 8 m/s (15 knots) are normal tropical breeze; 20+ m/s is squall/gale
    wind_score = min(1.0, max(0.0, (wind_speed_ms - 7.0) / 18.0))
    scores.append(("Wind", wind_score, 0.15))

    # Factor D: Atmospheric Pressure Anomaly (weight: 10%)
    # Tropical low pressure below 1010 hPa signals incoming storm cluster
    pressure_anomaly = max(0.0, 1013.25 - pressure_hpa) / 15.0
    pressure_score = min(1.0, max(0.0, pressure_anomaly))
    scores.append(("Pressure", pressure_score, 0.10))

    # Factor E: Soil Saturation (weight: 15%)
    # Soil saturation under 0.35 has high infiltration; > 0.75 is saturated
    soil_score = min(1.0, max(0.0, (soil_moisture - 0.30) / 0.70))
    scores.append(("Soil Saturation", soil_score, 0.15))

    # Weighted Composite Risk Score
    composite_score = sum(s * w for _, s, w in scores)

    # Compound Event Multiplier
    elevated_factors = sum(1 for _, s, _ in scores if s > 0.45)
    if elevated_factors >= 4:
        composite_score *= 1.35
    elif elevated_factors >= 3:
        composite_score *= 1.20
    composite_score = min(1.0, round(composite_score, 4))

    # 4. Physically Grounded Threshold Classification
    # True coastal overtopping check:
    physical_overtop = (
        effective_water_level_m >= critical_threshold_m and 
        effective_water_level_m >= (zone_elevation_m - freeboard_buffer)
    )

    if composite_score >= 0.60 or physical_overtop or pluvial_score >= 0.85:
        level = "red"
    elif composite_score >= 0.30 or effective_water_level_m >= ABSOLUTE_SURGE_THRESHOLDS["amber_max_m"] or pluvial_score >= 0.45:
        level = "amber"
    else:
        level = "green"

    return {
        "level": level,
        "score": composite_score,
        "effective_water_level_m": effective_water_level_m,
        "label": RISK_THRESHOLDS[level]["label"],
        "color": RISK_THRESHOLDS[level]["color"],
        "icon": RISK_THRESHOLDS[level]["icon"],
        "action": RISK_THRESHOLDS[level]["action"],
        "factor_scores": {name: round(score, 3) for name, score, _ in scores},
    }


def compute_zone_risks(water_level_m, rainfall_mm=0, wind_speed_ms=0,
                       pressure_hpa=1013, drainage_multiplier=1.0, soil_moisture=0.3,
                       blocked_zone_name=None):
    """
    Compute flood risk for ALL 20 Lagos Local Government Areas (macro level).
    """
    results = []
    for zone in LAGOS_ZONES:
        effective_drainage = zone.get("drainage_capacity", 0.5) * drainage_multiplier
        if blocked_zone_name and zone["name"] == blocked_zone_name:
            effective_drainage *= 0.25  # 75% reduction due to reported blockage

        risk = classify_risk_level(
            water_level_m=water_level_m,
            rainfall_mm=rainfall_mm,
            wind_speed_ms=wind_speed_ms,
            pressure_hpa=pressure_hpa,
            zone_elevation_m=zone["elevation_m"],
            zone_drainage_capacity=effective_drainage,
            soil_moisture=soil_moisture,
            distance_to_water_km=zone.get("distance_to_water_km", 1.0),
            critical_threshold_m=2.00
        )
        results.append({
            **zone,
            **risk,
            "risk_label": RISK_LABELS.get(risk["level"], risk["level"]),
            "people_at_risk": int(zone.get("population", 0) * risk.get("score", 0)),
        })

    # Sort by risk score (highest first)
    results.sort(key=lambda x: x["score"], reverse=True)
    return results


def compute_community_risks(water_level_m, rainfall_mm=0, wind_speed_ms=0,
                            pressure_hpa=1013, drainage_multiplier=1.0, soil_moisture=0.3,
                            blocked_zone_name=None):
    """
    Compute flood risk for granular communities and street hotspots across Lagos.
    Drills down from coarse LGAs into specific neighborhoods and street corridors.
    """
    results = []
    for comm in LAGOS_COMMUNITY_HOTSPOTS:
        effective_drainage = comm.get("drainage_capacity", 0.35) * drainage_multiplier
        if blocked_zone_name and (blocked_zone_name == comm["parent_lga"] or blocked_zone_name in comm["community"]):
            effective_drainage *= 0.25

        risk = classify_risk_level(
            water_level_m=water_level_m,
            rainfall_mm=rainfall_mm,
            wind_speed_ms=wind_speed_ms,
            pressure_hpa=pressure_hpa,
            zone_elevation_m=comm["elevation_m"],
            zone_drainage_capacity=effective_drainage,
            soil_moisture=soil_moisture,
            distance_to_water_km=comm.get("distance_to_water_km", 0.1),
            critical_threshold_m=comm.get("critical_threshold_m", 2.00)
        )

        results.append({
            **comm,
            **risk,
            "risk_label": RISK_LABELS.get(risk["level"], risk["level"]),
        })

    results.sort(key=lambda x: x["score"], reverse=True)
    return results


def find_community_or_zone(query: str, water_level_m, rainfall_mm=0, wind_speed_ms=0,
                           pressure_hpa=1013, soil_moisture=0.3):
    """
    Search for a specific street, community, or LGA by name and return its detailed risk assessment.
    Uses multi-stage token and subpart matching so queries like 'Is Victoria Island safe?' match reliably.
    """
    import re
    q = query.strip().lower()
    comms = compute_community_risks(water_level_m, rainfall_mm, wind_speed_ms, pressure_hpa, soil_moisture=soil_moisture)

    # 1. Check specific street hotspots and communities
    for c in comms:
        c_full = c["community"].lower()
        # Direct check
        if c_full in q:
            return c, "community"

        # Sub-phrases (e.g. split on brackets or slashes)
        subparts = [p.strip().lower() for p in re.split(r'[/&()]', c_full) if len(p.strip()) >= 4]
        for sp in subparts:
            if sp in q:
                return c, "community"

        # Meaningful tokens in community name
        ignore_words = {'town', 'road', 'axis', 'area', 'plain', 'strip', 'corridor', 'waters', 'market', 'highland', 'beach'}
        c_words = [w.strip() for w in re.split(r'[\s/&(),-]+', c_full) if len(w.strip()) >= 4 and w.strip() not in ignore_words]
        for w in c_words:
            if w in q:
                return c, "community"

        # Individual streets in hotspot_streets
        streets = [s.strip().lower() for s in c["hotspot_streets"].split(",")]
        for s in streets:
            if len(s) >= 4 and s in q:
                return c, "community"
            s_words = [w.strip() for w in re.split(r'[\s,]+', s) if len(w.strip()) >= 4 and w.strip() not in ignore_words]
            for sw in s_words:
                if sw in q:
                    return c, "community"

    # 2. Match in LGA zones
    zones = compute_zone_risks(water_level_m, rainfall_mm, wind_speed_ms, pressure_hpa, soil_moisture=soil_moisture)
    for z in zones:
        z_name = z["name"].lower()
        if z_name in q:
            return z, "zone"
        notables = [n.strip().lower() for n in z.get("notable_areas", "").split(",")]
        for n in notables:
            if len(n) >= 4 and n in q:
                return z, "zone"

    return None, None


def compute_risk_timeseries(dataset, zone_elevation_m=3.0):
    """
    Compute risk levels for every timestep in the dataset.
    Used for the Dashboard timeline view.
    """
    risk_levels = []
    risk_scores = []

    for idx, row in dataset.iterrows():
        risk = classify_risk_level(
            water_level_m=row.get("water_level_m", 0.5),
            rainfall_mm=row.get("rainfall_mm", 0),
            wind_speed_ms=row.get("wind_speed_ms", 0),
            pressure_hpa=row.get("pressure_hpa", 1013),
            zone_elevation_m=zone_elevation_m,
            soil_moisture=row.get("soil_moisture", 0.3),
        )
        risk_levels.append(risk["level"])
        risk_scores.append(risk["score"])

    dataset = dataset.copy()
    dataset["risk_level"] = risk_levels
    dataset["risk_score"] = risk_scores
    return dataset


def detect_compound_events(dataset, window_hours=24):
    """
    Detect compound flood events where multiple adverse factors coincide.
    """
    conditions = pd.DataFrame(index=dataset.index)

    wl_mean = dataset["water_level_m"].mean()
    wl_std = dataset["water_level_m"].std()

    conditions["high_water"] = (dataset["water_level_m"] > wl_mean + wl_std).astype(int)
    conditions["heavy_rain"] = (dataset["rainfall_mm"] > 15).astype(int)
    conditions["low_pressure"] = (dataset["pressure_hpa"] < 1010).astype(int)
    conditions["strong_wind"] = (dataset["wind_speed_ms"] > 10).astype(int)

    if "spring_tide_factor" in dataset.columns:
        conditions["spring_tide"] = (dataset["spring_tide_factor"] > 0.7).astype(int)
    elif "moon_phase" in dataset.columns:
        conditions["spring_tide"] = (
            (dataset["moon_phase"] < 0.15) | (dataset["moon_phase"] > 0.85)
        ).astype(int)
    else:
        conditions["spring_tide"] = 0

    conditions["n_factors"] = conditions.sum(axis=1)
    conditions["is_compound"] = (conditions["n_factors"] >= 3).astype(int)

    return conditions


def get_current_risk_summary(latest_data_row):
    """
    Get a dashboard-ready risk summary from the latest data point.
    """
    all_zones = compute_zone_risks(
        water_level_m=latest_data_row.get("water_level_m", 0.5),
        rainfall_mm=latest_data_row.get("rainfall_mm", 0),
        wind_speed_ms=latest_data_row.get("wind_speed_ms", 0),
        pressure_hpa=latest_data_row.get("pressure_hpa", 1013),
        soil_moisture=latest_data_row.get("soil_moisture", 0.3),
    )
    
    if all_zones:
        overall_risk = {
            "level": all_zones[0]["level"],
            "score": all_zones[0]["score"],
            "label": all_zones[0]["label"],
            "color": all_zones[0]["color"],
            "icon": all_zones[0]["icon"],
            "action": all_zones[0]["action"],
        }
    else:
        overall_risk = classify_risk_level(0.5, 0, 0, 1013, 3.0)

    red_zones = [z for z in all_zones if z["level"] == "red"]
    amber_zones = [z for z in all_zones if z["level"] == "amber"]
    green_zones = [z for z in all_zones if z["level"] == "green"]

    return {
        "overall_risk": overall_risk,
        "all_zones": all_zones,
        "n_red": len(red_zones),
        "n_amber": len(amber_zones),
        "n_green": len(green_zones),
        "most_at_risk": red_zones[0]["name"] if red_zones else (amber_zones[0]["name"] if amber_zones else "None"),
    }
