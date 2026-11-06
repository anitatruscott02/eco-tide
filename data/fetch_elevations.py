"""
Eco-Tide: Satellite Elevation Fetcher
Fetches real elevation data for all 20 Lagos LGAs from the Copernicus DEM
via the Open-Meteo Elevation API.

This replaces our hardcoded elevation estimates with scientifically accurate
30-meter resolution satellite-derived elevations.

Source: Copernicus Digital Elevation Model (DEM) via Open-Meteo
Resolution: 30 meters (SRTM-based)
"""

import sys
import os
import json
import requests

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config.settings import LAGOS_ZONES

ELEVATION_API = "https://api.open-meteo.com/v1/elevation"


def fetch_elevations():
    """Fetch real satellite elevations for all 20 Lagos LGAs."""
    print("🛰️  Fetching satellite elevations from Copernicus DEM...")
    print(f"   API: {ELEVATION_API}")
    print(f"   Zones: {len(LAGOS_ZONES)}")
    print()

    # Build batch request (all coordinates at once)
    lats = [z["lat"] for z in LAGOS_ZONES]
    lons = [z["lon"] for z in LAGOS_ZONES]

    params = {
        "latitude": ",".join(str(lat) for lat in lats),
        "longitude": ",".join(str(lon) for lon in lons),
    }

    response = requests.get(ELEVATION_API, params=params, timeout=30)
    response.raise_for_status()
    data = response.json()

    elevations = data.get("elevation", [])

    if len(elevations) != len(LAGOS_ZONES):
        print(f"❌ Expected {len(LAGOS_ZONES)} elevations, got {len(elevations)}")
        return None

    results = []
    for zone, elev in zip(LAGOS_ZONES, elevations):
        results.append({
            "name": zone["name"],
            "lat": zone["lat"],
            "lon": zone["lon"],
            "old_elevation_m": zone["elevation_m"],
            "satellite_elevation_m": round(elev, 1),
            "difference_m": round(elev - zone["elevation_m"], 1),
        })
        status = "✅" if abs(elev - zone["elevation_m"]) < 10 else "⚠️"
        print(f"   {status} {zone['name']:25s}  old={zone['elevation_m']:5.1f}m  "
              f"satellite={elev:5.1f}m  diff={elev - zone['elevation_m']:+.1f}m")

    print()
    print("=" * 70)
    print("SUMMARY")
    print("=" * 70)

    # Save results
    output_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "data", "raw", "satellite_elevations.json"
    )
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w") as f:
        json.dump(results, f, indent=2)
    print(f"   Saved to: {output_path}")

    # Generate the Python code to update settings.py
    print()
    print("📋 Copy-paste the following elevation updates into settings.py:")
    print("-" * 70)
    for r in results:
        print(f'    # {r["name"]}: Copernicus DEM = {r["satellite_elevation_m"]}m '
              f'(was {r["old_elevation_m"]}m)')

    return results


if __name__ == "__main__":
    results = fetch_elevations()
    if results:
        print()
        print("✅ Satellite elevation fetch complete!")
        print("   Source: Copernicus Digital Elevation Model (30m resolution)")
    else:
        print("❌ Failed to fetch elevations.")
