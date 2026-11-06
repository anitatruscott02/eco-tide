"""
Eco-Tide: Data Loader Utility
Centralized data loading with Streamlit caching for performance.
"""

import os
import sys
import time
import subprocess
import pandas as pd
import streamlit as st
from config.settings import PROCESSED_DATA_DIR, RAW_DATA_DIR, MODELS_DIR


@st.cache_data(ttl=1800)  # Cache for 30 minutes
def load_live_forecast():
    """Load live forecast data, fetching fresh if stale."""
    path = os.path.join(PROCESSED_DATA_DIR, "live_forecast.csv")
    script_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "fetch_live_forecast.py")
    
    # Check if live_forecast.csv exists and is less than 2 hours old
    needs_fetch = True
    if os.path.exists(path):
        file_age = time.time() - os.path.getmtime(path)
        if file_age < 7200:  # 2 hours
            needs_fetch = False
            
    if needs_fetch:
        try:
            # Run fetch_live_forecast with UTF-8 encoding
            subprocess.run([sys.executable, "-X", "utf8", script_path], check=True)
        except Exception as e:
            st.error(f"Failed to fetch live forecast: {e}")
            if not os.path.exists(path):
                return None
                
    if os.path.exists(path):
        df = pd.read_csv(path, index_col="datetime", parse_dates=True)
        return df
    return None

@st.cache_data(ttl=3600)
def load_dataset():
    """Load the main processed dataset."""
    path = os.path.join(PROCESSED_DATA_DIR, "eco_tide_dataset.csv")
    if not os.path.exists(path):
        st.error(f"Dataset not found at {path}. Please run data/fetch_real_data.py first.")
        st.stop()
    df = pd.read_csv(path, index_col="datetime", parse_dates=True)
    return df


@st.cache_data(ttl=3600)
def load_water_level_data():
    """Load the detailed water level data with surge components."""
    path = os.path.join(RAW_DATA_DIR, "water_level_with_surge.csv")
    if os.path.exists(path):
        return pd.read_csv(path, index_col="datetime", parse_dates=True)
    return None


@st.cache_data(ttl=3600)
def load_weather_data():
    """Load raw weather data."""
    path = os.path.join(RAW_DATA_DIR, "weather_data.csv")
    if os.path.exists(path):
        return pd.read_csv(path, index_col="datetime", parse_dates=True)
    return None


def load_model():
    """Load trained SARIMAX model."""
    import pickle
    path = os.path.join(MODELS_DIR, "sarimax_model.pkl")
    if not os.path.exists(path):
        return None
    with open(path, "rb") as f:
        return pickle.load(f)


def get_latest_data(dataset, n_hours=168):
    """Get the most recent n_hours of data."""
    return dataset.tail(n_hours)


def get_data_summary(dataset):
    """Get summary statistics of the dataset."""
    return {
        "total_records": len(dataset),
        "date_range_start": dataset.index.min().strftime("%Y-%m-%d"),
        "date_range_end": dataset.index.max().strftime("%Y-%m-%d"),
        "n_features": len(dataset.columns),
        "missing_pct": (dataset.isnull().sum().sum() / (len(dataset) * len(dataset.columns))) * 100,
    }


def check_and_auto_update_dataset(max_staleness_hours: int = 48, retrain_model: bool = False):
    """
    Check if the dataset has fallen behind real time. If so, automatically
    updates it in the background so old data is never used.
    """
    try:
        from data.auto_update_pipeline import get_dataset_freshness, run_pipeline_update
        freshness = get_dataset_freshness()
        if not freshness.get("is_fresh", False) and freshness.get("hours_behind", 0) > max_staleness_hours:
            run_pipeline_update(retrain_model=retrain_model)
            st.cache_data.clear()
    except Exception as e:
        print(f"Auto-update notice: {e}")

