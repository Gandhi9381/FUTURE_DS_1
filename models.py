from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Tuple

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error


@dataclass
class ForecastResult:
    forecast: pd.DataFrame
    metrics: Dict[str, float]
    model: object


def _aggregate_monthly(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["order_date"] = pd.to_datetime(df["order_date"]) if not np.issubdtype(df["order_date"].dtype, np.datetime64) else df["order_date"]
    monthly = df.set_index("order_date")["sales"].resample("M").sum().rename("y").reset_index()
    monthly["ds"] = monthly["order_date"].dt.to_period("M").dt.to_timestamp()
    return monthly[["ds", "y"]]


def _create_lag_features(series: pd.Series, n_lags: int) -> pd.DataFrame:
    df = pd.DataFrame({"y": series})
    for lag in range(1, n_lags + 1):
        df[f"lag_{lag}"] = df["y"].shift(lag)
    df = df.dropna().reset_index(drop=True)
    return df


def train_forecast_model(df: pd.DataFrame, horizon_months: int = 3, n_lags: int = 3) -> ForecastResult:
    """Train a simple RandomForest model on monthly aggregated sales and forecast ahead.

    Input df: expects columns `order_date`/`ds` and `sales`/`y`.
    Returns ForecastResult with forecast DataFrame containing `ds`, `y` (actual if available), and `y_pred`.
    """
    # Normalize column names
    working = df.copy()
    if "order_date" in working.columns and "y" not in working.columns:
        working = _aggregate_monthly(working)
    elif "ds" in working.columns and "y" in working.columns:
        working = working[["ds", "y"]].copy()
    else:
        raise ValueError("Dataframe must contain order_date/sales or ds/y columns")

    working = working.sort_values("ds").reset_index(drop=True)
    if len(working) < (n_lags + 2):
        raise ValueError("Not enough monthly records to train the model with requested lags")

    series = working["y"].copy()
    feat = _create_lag_features(series, n_lags)
    # align dates with features (drop first n_lags months)
    dates = working["ds"].iloc[n_lags:].reset_index(drop=True)
    feat["ds"] = dates

    # Split train/test using the last `horizon_months` as holdout
    if horizon_months >= len(feat):
        train_feat = feat.iloc[:-1]
        test_feat = feat.iloc[-1:]
    else:
        train_feat = feat.iloc[:-horizon_months]
        test_feat = feat.iloc[-horizon_months:]

    X_train = train_feat[[c for c in train_feat.columns if c.startswith("lag_")]]
    y_train = train_feat["y"]
    X_test = test_feat[[c for c in test_feat.columns if c.startswith("lag_")]]
    y_test = test_feat["y"]

    model = RandomForestRegressor(n_estimators=200, random_state=42)
    model.fit(X_train, y_train)

    # Predict on test set
    y_pred_test = model.predict(X_test) if len(X_test) > 0 else np.array([])
    mae = mean_absolute_error(y_test, y_pred_test) if len(y_test) > 0 else float("nan")
    rmse = float(np.sqrt(mean_squared_error(y_test, y_pred_test))) if len(y_test) > 0 else float("nan")

    # Iterative forecasting for horizon
    last_known = series.values[-n_lags:].tolist()
    forecasts = []
    for i in range(horizon_months):
        X_pred = np.array(last_known[-n_lags:])[::-1].reshape(1, -1)
        y_next = model.predict(X_pred)[0]
        forecasts.append(y_next)
        last_known.append(y_next)

    # Build forecast DataFrame
    last_date = working["ds"].max()
    future_dates = pd.date_range(last_date + pd.offsets.MonthBegin(1), periods=horizon_months, freq="MS")
    forecast_df = pd.DataFrame({"ds": list(working["ds"]) + list(future_dates),
                                "y": list(working["y"]) + [None] * horizon_months})
    preds = list(np.concatenate([np.array([np.nan] * len(working)), np.array(forecasts)]))
    # attach predictions column aligned to forecast_df
    forecast_df["y_pred"] = preds
    forecast_df["is_forecast"] = [False] * len(working) + [True] * horizon_months

    metrics = {"mae": float(mae), "rmse": float(rmse)}
    return ForecastResult(forecast=forecast_df, metrics=metrics, model=model)
