"""Comparable sales-only versus sales-plus-market Ridge evaluation.

This module is intentionally callable, rather than wired into the historical
pipeline, so existing benchmark outputs are never changed without real overlap.
"""

import numpy as np
import pandas as pd
from sklearn.linear_model import Ridge
from sklearn.metrics import mean_absolute_error, mean_squared_error


MARKET_FEATURE_COLUMNS = [
    "market_price", "price_change_1d", "price_change_7d", "price_change_14d",
    "price_change_30d", "price_change_pct_7d", "price_change_pct_14d",
    "price_change_pct_30d", "price_volatility_7d", "price_volatility_30d",
]


def _metrics(actual: np.ndarray, prediction: np.ndarray) -> dict[str, float]:
    prediction = np.clip(prediction, 0, None)
    return {
        "mae": float(mean_absolute_error(actual, prediction)),
        "rmse": float(np.sqrt(mean_squared_error(actual, prediction))),
        "wape": float(np.abs(actual - prediction).sum() / actual.sum() * 100) if actual.sum() else 0.0,
    }


def evaluate_ridge_sales_vs_market(
    features: pd.DataFrame, sales_feature_columns: list[str], *, split_date: str | pd.Timestamp
) -> dict[str, dict[str, float]]:
    """Evaluate two Ridge configurations on one chronological split.

    `features` must already be an as-of join: a market value on date T may only
    originate from an observation dated <= T. Missing market rows are rejected,
    rather than imputed with invented price data.
    """
    needed = {"date_", "daily_quantity", *sales_feature_columns, *MARKET_FEATURE_COLUMNS}
    missing = needed.difference(features.columns)
    if missing:
        raise ValueError(f"Missing required features: {sorted(missing)}")
    frame = features.copy()
    frame["date_"] = pd.to_datetime(frame["date_"])
    frame = frame.dropna(subset=MARKET_FEATURE_COLUMNS)
    if frame.empty:
        raise ValueError("No rows have sufficient overlapping market-price history")
    split = pd.Timestamp(split_date)
    train, validation = frame[frame.date_ < split], frame[frame.date_ >= split]
    if train.empty or validation.empty:
        raise ValueError("Chronological split leaves no train or validation rows")
    y_train, y_validation = train.daily_quantity.to_numpy(), validation.daily_quantity.to_numpy()
    sales_model = Ridge(alpha=1.0).fit(train[sales_feature_columns], y_train)
    market_model = Ridge(alpha=1.0).fit(train[sales_feature_columns + MARKET_FEATURE_COLUMNS], y_train)
    return {
        "sales_only": _metrics(y_validation, sales_model.predict(validation[sales_feature_columns])),
        "sales_plus_market": _metrics(y_validation, market_model.predict(validation[sales_feature_columns + MARKET_FEATURE_COLUMNS])),
        "rows": {"train": int(len(train)), "validation": int(len(validation))},
    }
