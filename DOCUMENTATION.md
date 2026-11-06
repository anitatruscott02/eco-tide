# 🌊 Eco-Tide: Technical & Operational System Documentation
**AI & Physics-Powered Coastal & Pluvial Flood Early Warning System for Lagos State**

---

## 📌 Executive Summary
**Eco-Tide** is an operational early warning decision support system built to predict, analyze, and monitor coastal storm surges and pluvial flood risks across the **20 Local Government Areas (LGAs) of Lagos State, Nigeria**. 

Because physical tidal gauges in the Gulf of Guinea (such as NIWA tide stations) often suffer from telemetry dropouts, siltation, or hardware failure, Eco-Tide operates on a **"Software-First GeoAI" paradigm**. It combines:
1. **Copernicus 30m Digital Elevation Models (DEM)** and Sentinel-2 satellite imagery.
2. **Open-Meteo & ERA5 atmospheric reanalysis & live 7-day numerical forecasts**.
3. **Harmonic Astronomical Tidal constituent synthesis** calibrated to the Lagos Bight.
4. **Physically-grounded Compound Risk Engine** accounting for wind setup, barometric surge, rainfall runoff, and soil saturation.
5. **SARIMAX AI Forecasting Model** predicting 24-to-48-hour water levels.
6. **Mobile Geolocation & Multilingual Community Response Hub** connected to Supabase for real-time crowdsourced flood telemetry.

---

## 🗂️ Project Directory & File Paths

* **Project Root Directory:**
  `C:\Users\Starfix-geo\.gemini\antigravity\scratch\eco-tide`
* **Local Web Interface:**
  `http://localhost:8501`

### Directory Architecture
```text
eco-tide/
├── app.py                             # Main Streamlit application entry point & router
├── requirements.txt                   # Production Python package dependencies
├── DOCUMENTATION.md                   # Complete application guide and architecture docs
├── fix_tabs.py                        # Automated patch script for Community Chat integration
├── .streamlit/
│   ├── config.toml                    # Server theme and port settings
│   └── secrets.toml.example           # Supabase credentials template
├── config/
│   └── settings.py                    # Lagos LGA spatial metadata, tide harmonics, alert thresholds
├── data/
│   ├── fetch_real_data.py             # Historical multi-source data ingestion pipeline (5 years)
│   ├── fetch_live_forecast.py         # Live 7-day atmospheric & marine forecast synchronizer
│   ├── fetch_elevations.py            # Copernicus DEM elevation retriever per LGA
│   ├── raw/                           # Raw atmospheric, marine, and elevation data
│   ├── processed/
│   │   ├── eco_tide_dataset.csv       # Primary 43,000+ row historical hourly training dataset
│   │   └── live_forecast.csv          # Real-time rolling 168-hour forecast
│   └── satellite/                     # Sentinel-2 true-color & NDWI flood visualization maps
├── models/
│   ├── risk_engine.py                 # Compound physics-based flood risk scoring engine
│   ├── sarimax_model.py               # AI time-series forecasting model (SARIMAX)
│   ├── tidal_analysis.py              # Astronomical harmonic tide constituent processor
│   └── saved/
│       └── sarimax_model.pkl          # Serialized production forecasting model
├── components/
│   ├── geolocation.py                 # HTML5/JS mobile browser GPS widget & Haversine matcher
│   ├── charts.py                      # Theme-aware Plotly charts (surges, rainfall, risk breakdown)
│   ├── metrics_cards.py               # KPI summary display cards
│   └── traffic_light.py               # Dynamic LGA status & alert badges
├── pages/
│   ├── 1_🌊_Dashboard.py              # Central executive control room & 7-day live risk view
│   ├── 2_📊_Analysis.py               # Exploratory data analysis, surge distributions & correlations
│   ├── 3_🔮_Predictions.py            # 48-hour SARIMAX forecast & Climate Stress Test Analysis
│   ├── 4_🗺️_Risk_Map.py              # Interactive Folium map of all 20 LGAs with elevation overlays
│   ├── 5_📈_Model_Performance.py      # AI regression validation metrics (RMSE, MAE, R²)
│   ├── 6_📅_Disaster_Replay.py        # Historical replay of landmark floods (2021, 2022, 2023)
│   ├── 7_📖_Methodology.py            # Scientific GeoAI documentation & formula derivations
│   ├── 8_🚨_Community_Response.py     # Public safety checklists, evacuation routes & contacts
│   └── 9_💬_Community_Chat.py         # AI Assistant (English, Yoruba, Igbo, Hausa) & Mobile GPS hub
└── utils/
    ├── data_loader.py                 # Cached dataset ingestion and pipeline validation
    ├── supabase_client.py             # Dual-engine backend: Supabase cloud DB + local fallback
    ├── theme.py                       # Conjugated Dark / Bright CSS styling engine
    └── translations.py                # 4-language emergency response corpus
```

---

## ⚙️ Core Modules & Scientific Methodology

### 1. The Physics Risk Engine (`models/risk_engine.py`)
Rather than relying solely on black-box heuristics, Eco-Tide classifies compound flood risk using hydrodynamic and hydrological formulas:

1. **Inverse Barometer Effect (IBE):**
   $$\Delta \eta_{\text{IBE}} = (1013.25 - P_{\text{hPa}}) \times 0.01 \text{ m}$$
   A 1 hPa atmospheric drop induces approximately 1 cm of static sea surface rise.

2. **Wind Setup (Storm Surge):**
   Derived from the simplified Zuiderzee equation across the Lagos shelf:
   $$S_{\text{wind}} = \frac{U_{10}^2 \cdot F}{g \cdot D}$$
   Where $U_{10}$ is the 10-meter wind speed, $F$ is effective fetch (derived from coastal proximity), $g$ is gravitational acceleration ($9.81\text{ m/s}^2$), and $D$ is mean bathymetric depth.

3. **Pluvial Surface Runoff & Soil Saturation:**
   Runoff coefficient $C_{\text{runoff}}$ adjusts dynamically based on upper soil layer moisture (0–7 cm):
   $$C_{\text{runoff}} = 0.20 + 0.80 \times S_{\text{moisture}}$$
   Pluvial pressure is then evaluated against the LGA's engineered drainage capacity:
   $$R_{\text{pluvial}} = \min\left(\frac{R_{\text{mm}} \times C_{\text{runoff}}}{100 \times \text{drainage\_capacity}}, 1.0\right)$$

4. **Compound Event Multiplier:**
   When multiple hazard drivers (storm surge, torrential precipitation, saturated soil, spring tides) occur simultaneously, risk amplifies non-linearly:
   - $\ge 3$ factors above 50% severity $\rightarrow$ **$1.25\times$ risk multiplier**
   - $\ge 4$ factors above 50% severity $\rightarrow$ **$1.50\times$ risk multiplier**

---

### 2. The AI Forecasting Pipeline (`models/sarimax_model.py`)
- **Architecture:** Seasonal AutoRegressive Integrated Moving Average with eXogenous regressors ($\text{SARIMAX}(p, d, q)(P, D, Q)_s$).
- **Exogenous Regressors:** Wind velocity ($U, V$), sea surface temperature, barometric pressure anomaly, and synthesized astronomical tide.
- **Horizon:** 24-hour to 48-hour forward projection with 95% confidence intervals.
- **Validation Metrics:** Evaluated against held-out historical storm surges, tracking RMSE, Mean Absolute Error (MAE), and $R^2$ score.

---

### 3. Dual-Engine Database & Supabase Integration (`utils/supabase_client.py`)
Eco-Tide supports resilient telemetry storage:
* **Cloud Mode (Supabase):** When `.streamlit/secrets.toml` or environment variables provide `SUPABASE_URL` and `SUPABASE_KEY`, reports stream directly to the `community_reports` table via Supabase's PostgREST API.
* **Offline Resilient Mode:** If cloud credentials are absent or network drops, all incident submissions and chat histories persist to structured JSON files (`data/local_community_reports.json` and `data/local_chat_history.json`).

#### Captured Report Schema
```json
{
  "lga": "Eti-Osa",
  "reporter": "Lekki Community Warden",
  "severity": "High",
  "water_cm": "35 cm",
  "msg": "Drainage canal overflow along Admiralty Way.",
  "lat": 6.43214,
  "lon": 3.43856,
  "accuracy_m": 12.5,
  "created_at": "2026-10-14T17:30:00Z"
}
```

---

### 4. Mobile GPS Geolocation (`components/geolocation.py`)
When viewed on a mobile device or desktop browser:
1. The user taps **"📍 Share My Location"**.
2. The browser executes standard HTML5 `navigator.geolocation.getCurrentPosition()`.
3. High-precision coordinates (`lat`, `lon`, `accuracy`) are bridged into Python.
4. The **Haversine Great-Circle distance formula** dynamically identifies the nearest of the 20 Lagos LGAs:
   $$d = 2R \arcsin\left(\sqrt{\sin^2\left(\frac{\Delta \phi}{2}\right) + \cos(\phi_1)\cos(\phi_2)\sin^2\left(\frac{\Delta \lambda}{2}\right)}\right)$$
5. The interface automatically updates the **"Your Area Risk"** card with the exact real-time risk status, drainage metrics, and evacuation recommendations for that LGA.

---

### 5. Multilingual Public Interface
In emergency scenarios, accessibility is vital. The interface and AI Emergency Assistant provide native guidance in:
- 🇬🇧 **English**
- 🇳🇬 **Yorùbá**
- 🇳🇬 **Igbo**
- 🇳🇬 **Hausa**

---

## 🚀 How to Run and Maintain the Application

### 1. Launch the Application
Run from PowerShell or terminal:
```powershell
cd C:\Users\Starfix-geo\.gemini\antigravity\scratch\eco-tide
python -m streamlit run app.py --server.port 8501 --server.headless true
```
Open your browser at **`http://localhost:8501`**.

### 2. Update Live Weather & Marine Forecasts
To manually trigger a 7-day synchronization with Open-Meteo APIs:
```powershell
python data/fetch_live_forecast.py
```

### 3. Connect Supabase (Optional)
To point incident reports and chat records to your Supabase instance, create `.streamlit/secrets.toml`:
```toml
SUPABASE_URL = "https://your-project-id.supabase.co"
SUPABASE_KEY = "your-anon-or-service-role-key"
```

---

## 🛡️ Emergency Contacts Reference
* **LASEMA (Lagos State Emergency Management Agency):** `767` or `112`
* **NEMA (National Emergency Management Agency):** `0800-CALL-NEMA (0800-2255-6362)`
* **Federal Fire Service:** `01-7944927`
* **Nigerian Red Cross (Lagos Branch):** `01-8700920`
