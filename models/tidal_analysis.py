"""
Eco-Tide: Tidal Harmonic Analysis Module
Decomposes observed water levels into deterministic tidal signal and residual.

Uses superposition of known Lagos tidal constituents (M2, S2, K1, O1, N2, K2).
When UTide is available, performs full harmonic analysis.
"""

import numpy as np
import pandas as pd
from config.settings import TIDAL_CONSTITUENTS, MEAN_SEA_LEVEL_M


def harmonic_predict(dates, constituents=None):
    """
    Predict tidal water levels from harmonic constituents.

    Args:
        dates: pd.DatetimeIndex of prediction times
        constituents: dict of constituent parameters (default: Lagos settings)

    Returns:
        pd.Series of predicted tidal water levels (meters)
    """
    if constituents is None:
        constituents = TIDAL_CONSTITUENTS

    # Reference time (first date)
    t0 = dates[0]
    hours = np.array([(dt - t0).total_seconds() / 3600.0 for dt in dates])

    # Superposition of all constituents
    water_level = np.full(len(dates), MEAN_SEA_LEVEL_M)

    for name, params in constituents.items():
        amp = params["amplitude_m"]
        phase = np.radians(params["phase_deg"])
        period = params["period_hr"]
        angular_freq = 2 * np.pi / period

        water_level += amp * np.cos(angular_freq * hours - phase)

    return pd.Series(water_level, index=dates, name="tidal_prediction")


def extract_residual(observed, predicted):
    """
    Calculate the non-tidal residual (meteorological surge).

    residual = observed - predicted_tidal
    This residual contains the weather-driven component that SARIMAX will model.
    """
    common_idx = observed.index.intersection(predicted.index)
    residual = observed.loc[common_idx] - predicted.loc[common_idx]
    return residual


def get_constituent_table():
    """
    Return a formatted table of tidal constituents for display.
    """
    rows = []
    for name, params in TIDAL_CONSTITUENTS.items():
        rows.append({
            "Constituent": name,
            "Amplitude (m)": f"{params['amplitude_m']:.4f}",
            "Phase (°)": f"{params['phase_deg']:.1f}",
            "Period (hr)": f"{params['period_hr']:.4f}",
            "Type": "Semidiurnal" if params["period_hr"] < 14 else "Diurnal",
        })
    return pd.DataFrame(rows)


def compute_tidal_range(dates, constituents=None):
    """Compute tidal range statistics for a given period."""
    prediction = harmonic_predict(dates, constituents)
    return {
        "mean_level": prediction.mean(),
        "max_high_tide": prediction.max(),
        "min_low_tide": prediction.min(),
        "tidal_range": prediction.max() - prediction.min(),
        "std_dev": prediction.std(),
    }


def analyze_tidal_signal(observed_water_level):
    """
    Full tidal analysis pipeline:
    1. Predict tidal component
    2. Extract residual
    3. Compute statistics

    Args:
        observed_water_level: pd.Series with datetime index

    Returns:
        dict with tidal_prediction, residual, and statistics
    """
    tidal_pred = harmonic_predict(observed_water_level.index)
    residual = extract_residual(observed_water_level, tidal_pred)

    stats = {
        "tidal_range": tidal_pred.max() - tidal_pred.min(),
        "max_residual": residual.max(),
        "min_residual": residual.min(),
        "residual_std": residual.std(),
        "residual_mean": residual.mean(),
        "correlation": np.corrcoef(
            observed_water_level.loc[residual.index],
            tidal_pred.loc[residual.index]
        )[0, 1],
    }

    return {
        "tidal_prediction": tidal_pred,
        "residual": residual,
        "statistics": stats,
        "constituents": get_constituent_table(),
    }
