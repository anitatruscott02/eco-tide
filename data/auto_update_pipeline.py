"""
Eco-Tide: Automated Continuous Data Pipeline & Model Retraining Engine
Keeps the dataset and AI model perpetually up-to-date with live satellite and
meteorological observations. Can be executed:
  1. Programmatically via utils.data_loader on app startup / staleness check
  2. Interactively via the Streamlit UI (Model Performance page)
  3. Automatically via scheduled cron / Windows Task Scheduler / GitHub Actions
"""

import os
import sys
from datetime import datetime, timedelta
import pandas as pd

# Add project root to sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from config.settings import (
    DATA_START_DATE, PROCESSED_DATA_DIR, RAW_DATA_DIR, MODELS_DIR
)


def get_dataset_freshness() -> dict:
    """Check the current date range and freshness of the processed dataset."""
    path = os.path.join(PROCESSED_DATA_DIR, "eco_tide_dataset.csv")
    if not os.path.exists(path):
        return {
            "exists": False,
            "records": 0,
            "start": None,
            "end": None,
            "hours_behind": 9999,
            "is_fresh": False,
        }

    try:
        # Read only index column to be fast
        df = pd.read_csv(path, usecols=["datetime"], parse_dates=["datetime"])
        max_dt = df["datetime"].max()
        min_dt = df["datetime"].min()
        now = datetime.now()
        hours_behind = max(0, int((now - max_dt).total_seconds() / 3600))
        is_fresh = hours_behind <= 24

        return {
            "exists": True,
            "records": len(df),
            "start": min_dt.strftime("%Y-%m-%d"),
            "end": max_dt.strftime("%Y-%m-%d %H:%M"),
            "max_date": max_dt.strftime("%Y-%m-%d"),
            "hours_behind": hours_behind,
            "is_fresh": is_fresh,
        }
    except Exception as e:
        return {
            "exists": True,
            "records": 0,
            "start": None,
            "end": None,
            "hours_behind": 9999,
            "is_fresh": False,
            "error": str(e),
        }


def run_pipeline_update(retrain_model: bool = True, progress_callback=None) -> dict:
    """
    Fetch the latest observations from Open-Meteo, regenerate derived tidal and
    surge physics, update the processed dataset, and optionally retrain SARIMAX.

    Returns:
        dict: summary of the update results.
    """
    def log(msg):
        print(f"🌊 [Eco-Tide Auto-Sync] {msg}")
        if progress_callback:
            progress_callback(msg)

    log("Starting automated data synchronization...")

    # Step 1: Update settings end date
    today_str = datetime.now().strftime("%Y-%m-%d")
    log(f"Targeting date range: {DATA_START_DATE} through {today_str}")

    # Step 2: Run fetch_real_data
    from data.fetch_real_data import main as run_fetch
    log("Fetching fresh meteorological and marine data from Open-Meteo...")
    merged_df = run_fetch()

    result = {
        "success": True,
        "records": len(merged_df),
        "start_date": str(merged_df.index.min()),
        "end_date": str(merged_df.index.max()),
        "model_retrained": False,
    }

    # Step 3: Retrain SARIMAX model if requested
    if retrain_model:
        log("Retraining SARIMAX AI model on updated observations...")
        from models.sarimax_model import train_model_pipeline
        model_results, eval_result, _ = train_model_pipeline(merged_df)
        result["model_retrained"] = True
        result["metrics"] = eval_result.get("metrics", {})
        log("Model retraining complete and weights saved!")

    log("Automated synchronization finished successfully!")
    return result


if __name__ == "__main__":
    freshness = get_dataset_freshness()
    print("Current Dataset Freshness:", freshness)
    print("Running auto-update...")
    res = run_pipeline_update(retrain_model=True)
    print("Result:", res)
