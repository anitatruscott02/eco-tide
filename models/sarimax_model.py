"""
Eco-Tide: SARIMAX Model for Meteorological Surge Prediction
Models the non-tidal residual (weather-driven component) using SARIMAX
with environmental exogenous variables.

Hybrid approach: UTide handles tides → SARIMAX handles weather surge
"""

import os
import pickle
import warnings
import numpy as np
import pandas as pd
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
from sklearn.preprocessing import StandardScaler

warnings.filterwarnings("ignore")

import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config.settings import SARIMAX_CONFIG, EXOGENOUS_FEATURES, MODELS_DIR


def prepare_model_data(dataset, target_col="met_surge_m", test_fraction=0.2):
    """
    Prepare data for SARIMAX model training.

    Args:
        dataset: pd.DataFrame with all features
        target_col: column to predict (meteorological surge residual)
        test_fraction: fraction of data for testing

    Returns:
        dict with train/test splits and scaler
    """
    # Select available exogenous features
    available_features = [f for f in EXOGENOUS_FEATURES if f in dataset.columns]
    if not available_features:
        # Fallback features
        available_features = [c for c in dataset.columns
                              if c not in [target_col, "water_level_m", "tidal_component_m",
                                           "tidal_signal_m", "pressure_surge_m", "wind_surge_m",
                                           "rainfall_surge_m"]]
        available_features = available_features[:8]  # Limit to prevent overfitting

    print(f"   Using {len(available_features)} exogenous features: {available_features}")

    # Ensure target exists
    if target_col not in dataset.columns:
        print(f"   ⚠️  {target_col} not found. Using water_level_m as target.")
        target_col = "water_level_m"

    # Clean data
    df = dataset[[target_col] + available_features].dropna()

    # Train/test split (time-series: no shuffle!)
    split_idx = int(len(df) * (1 - test_fraction))
    train = df.iloc[:split_idx]
    test = df.iloc[split_idx:]

    # Scale exogenous features
    scaler = StandardScaler()
    train_exog = pd.DataFrame(
        scaler.fit_transform(train[available_features]),
        columns=available_features,
        index=train.index
    )
    test_exog = pd.DataFrame(
        scaler.transform(test[available_features]),
        columns=available_features,
        index=test.index
    )

    return {
        "train_endog": train[target_col],
        "test_endog": test[target_col],
        "train_exog": train_exog,
        "test_exog": test_exog,
        "scaler": scaler,
        "features": available_features,
        "target_col": target_col,
        "split_idx": split_idx,
    }


def train_sarimax(data_dict, use_auto=True):
    """
    Train SARIMAX model on the meteorological surge residual.

    Args:
        data_dict: output from prepare_model_data()
        use_auto: if True, use pmdarima auto_arima for parameter selection

    Returns:
        fitted model results
    """
    import statsmodels.api as sm

    train_y = data_dict["train_endog"]
    train_X = data_dict["train_exog"]

    if use_auto:
        try:
            import pmdarima as pm
            print("   🔍 Running auto_arima for optimal (p,d,q)(P,D,Q,s) selection...")

            # Use a subset for faster auto_arima (first 2000 points)
            n_auto = min(2000, len(train_y))
            auto_model = pm.auto_arima(
                y=train_y.iloc[:n_auto],
                X=train_X.iloc[:n_auto],
                start_p=0, max_p=SARIMAX_CONFIG["max_p"],
                d=None,
                start_q=0, max_q=SARIMAX_CONFIG["max_q"],
                seasonal=True,
                start_P=0, max_P=SARIMAX_CONFIG["max_P"],
                D=None,
                start_Q=0, max_Q=SARIMAX_CONFIG["max_Q"],
                m=SARIMAX_CONFIG["seasonal_period"],
                information_criterion=SARIMAX_CONFIG["information_criterion"],
                stepwise=SARIMAX_CONFIG["stepwise"],
                suppress_warnings=True,
                error_action="ignore",
                trace=False,
            )
            order = auto_model.order
            seasonal_order = auto_model.seasonal_order
            print(f"   ✅ Auto-selected: SARIMAX{order}x{seasonal_order}")
        except ImportError:
            print("   ⚠️  pmdarima not available. Using default parameters.")
            order = (1, 1, 1)
            seasonal_order = (1, 0, 1, 24)
    else:
        order = (1, 1, 1)
        seasonal_order = (1, 0, 1, 24)
        print(f"   Using default: SARIMAX{order}x{seasonal_order}")

    # Fit SARIMAX model on full training data
    print(f"   🏋️ Training SARIMAX on {len(train_y)} hourly records...")
    model = sm.tsa.statespace.SARIMAX(
        endog=train_y,
        exog=train_X,
        order=order,
        seasonal_order=seasonal_order,
        enforce_stationarity=False,
        enforce_invertibility=False,
    )

    results = model.fit(disp=False, maxiter=200)
    print(f"   ✅ Model trained. AIC: {results.aic:.2f}, BIC: {results.bic:.2f}")

    return results, order, seasonal_order


def evaluate_model(results, data_dict):
    """
    Evaluate SARIMAX model on test set and compute metrics.
    """
    test_y = data_dict["test_endog"]
    test_X = data_dict["test_exog"]

    # Generate predictions
    predictions = results.get_forecast(steps=len(test_y), exog=test_X)
    pred_mean = predictions.predicted_mean
    conf_int = predictions.conf_int()

    # Compute metrics
    rmse = np.sqrt(mean_squared_error(test_y, pred_mean))
    mae = mean_absolute_error(test_y, pred_mean)
    r2 = r2_score(test_y, pred_mean)
    nrmse = rmse / (test_y.max() - test_y.min()) if (test_y.max() - test_y.min()) > 0 else 0
    correlation = np.corrcoef(test_y, pred_mean)[0, 1] if len(test_y) > 1 else 0

    # Naive persistence baseline (predict next = current)
    naive_pred = test_y.shift(1).dropna()
    naive_actual = test_y.iloc[1:]
    naive_rmse = np.sqrt(mean_squared_error(naive_actual, naive_pred))

    metrics = {
        "rmse": rmse,
        "mae": mae,
        "r2": r2,
        "nrmse": nrmse,
        "correlation": correlation,
        "aic": results.aic,
        "bic": results.bic,
        "naive_rmse": naive_rmse,
        "skill_score": 1 - (rmse / naive_rmse) if naive_rmse > 0 else 0,
        "n_train": len(data_dict["train_endog"]),
        "n_test": len(test_y),
    }

    print(f"\n   📊 Model Evaluation Metrics:")
    print(f"      RMSE:         {rmse:.4f} m")
    print(f"      MAE:          {mae:.4f} m")
    print(f"      R²:           {r2:.4f}")
    print(f"      NRMSE:        {nrmse:.4f}")
    print(f"      Correlation:  {correlation:.4f}")
    print(f"      Naive RMSE:   {naive_rmse:.4f} m")
    print(f"      Skill Score:  {metrics['skill_score']:.4f}")
    print(f"      {'✅ Model beats naive baseline!' if rmse < naive_rmse else '⚠️ Model does not beat baseline.'}")

    return {
        "predictions": pred_mean,
        "confidence_intervals": conf_int,
        "actual": test_y,
        "metrics": metrics,
    }


def save_model(results, data_dict, metrics, order, seasonal_order):
    """Save trained model and metadata."""
    os.makedirs(MODELS_DIR, exist_ok=True)

    model_data = {
        "results": results,
        "scaler": data_dict["scaler"],
        "features": data_dict["features"],
        "target_col": data_dict["target_col"],
        "order": order,
        "seasonal_order": seasonal_order,
        "metrics": metrics,
    }

    path = os.path.join(MODELS_DIR, "sarimax_model.pkl")
    with open(path, "wb") as f:
        pickle.dump(model_data, f)
    print(f"   💾 Model saved to {path}")
    return path


def load_model():
    """Load trained model."""
    path = os.path.join(MODELS_DIR, "sarimax_model.pkl")
    if not os.path.exists(path):
        return None
    with open(path, "rb") as f:
        return pickle.load(f)


def forecast(results, exog_future, tidal_future, n_steps=48):
    """
    Generate combined flood forecast.

    final_forecast = tidal_prediction + SARIMAX_residual_prediction

    Args:
        results: fitted SARIMAX model
        exog_future: DataFrame of future exogenous variables (n_steps rows)
        tidal_future: Series of future tidal predictions
        n_steps: number of hours to forecast

    Returns:
        DataFrame with forecast, components, and confidence intervals
    """
    # Get SARIMAX forecast of the residual
    forecast_result = results.get_forecast(steps=n_steps, exog=exog_future.iloc[:n_steps])
    residual_forecast = forecast_result.predicted_mean
    conf_int = forecast_result.conf_int()

    # Combine with tidal prediction
    total_forecast = tidal_future.iloc[:n_steps].values + residual_forecast.values

    forecast_df = pd.DataFrame({
        "total_forecast_m": total_forecast,
        "tidal_component_m": tidal_future.iloc[:n_steps].values,
        "surge_forecast_m": residual_forecast.values,
        "lower_ci_m": tidal_future.iloc[:n_steps].values + conf_int.iloc[:, 0].values,
        "upper_ci_m": tidal_future.iloc[:n_steps].values + conf_int.iloc[:, 1].values,
    }, index=residual_forecast.index)

    return forecast_df


def train_model_pipeline(dataset):
    """
    Full model training pipeline.
    Call this from the data pipeline or Streamlit app.
    """
    print("\n" + "=" * 70)
    print("🤖 SARIMAX MODEL TRAINING PIPELINE")
    print("=" * 70)

    # Prepare data
    print("\n📦 Preparing model data...")
    data_dict = prepare_model_data(dataset)

    # Train
    print("\n🏋️ Training SARIMAX model...")
    results, order, seasonal_order = train_sarimax(data_dict, use_auto=True)

    # Evaluate
    print("\n📊 Evaluating model...")
    eval_result = evaluate_model(results, data_dict)

    # Save
    print("\n💾 Saving model...")
    save_model(results, data_dict, eval_result["metrics"], order, seasonal_order)

    print("\n" + "=" * 70)
    print("✅ MODEL TRAINING COMPLETE!")
    print("=" * 70)

    return results, eval_result, data_dict
