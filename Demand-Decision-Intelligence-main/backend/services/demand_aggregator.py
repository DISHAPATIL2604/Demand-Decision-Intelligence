"""
backend/services/demand_aggregator.py
---------------------------------------
Daily Demand Aggregation Service.

Converts a validated/cleaned sales DataFrame into a daily aggregated
demand DataFrame, grouped by (date_, product_id, city_name).

This is the output that the ML forecasting team consumes as their input
time series. The output schema intentionally mirrors the ML team's
existing daily_product_demand.csv plus extra price/discount features.

Aggregation rules (from PRD & DECISIONS.md D-009):
    total_quantity  = SUM(procured_quantity)
    revenue         = SUM(procured_quantity × unit_selling_price)
    avg_unit_price  = revenue / total_quantity   (revenue-weighted avg)
    avg_discount    = AVG(total_discount_amount) (simple average per group)
    order_count     = COUNT(DISTINCT order_id)

Zero-fill:
    If fill_missing_dates=True, the date range for each (product, city)
    pair is expanded to cover every calendar day within the product's
    active period. Missing days are filled with zeros. This flag is False
    by default and should only be set True when the ML team explicitly
    needs continuous time series.

Public API
----------
    agg_df = aggregate_daily(valid_df, fill_missing_dates=False)
"""

from __future__ import annotations

import logging
from typing import Optional

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Column constants
# ---------------------------------------------------------------------------

GROUP_KEYS = ["date_", "product_id", "city_name"]

OUTPUT_COLUMNS = [
    "date_",
    "product_id",
    "city_name",
    "total_quantity",
    "revenue",
    "avg_unit_price",
    "avg_discount",
    "order_count",
    "is_zero_filled",
]


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------

def aggregate_daily(
    valid_df: pd.DataFrame,
    fill_missing_dates: bool = False,
) -> pd.DataFrame:
    """
    Aggregate a validated sales DataFrame to daily demand per product per city.

    Parameters
    ----------
    valid_df : pd.DataFrame
        Output of upload_validator.validate_and_clean().valid_df.
        Expected columns: date_, product_id, city_name,
                          procured_quantity, unit_selling_price,
                          total_discount_amount, order_id.
    fill_missing_dates : bool
        If True, expand each (product_id, city_name) pair to a continuous
        date range and fill missing days with zero demand.
        Default is False.

    Returns
    -------
    pd.DataFrame
        One row per (date_, product_id, city_name) with columns:
        date_, product_id, city_name, total_quantity, revenue,
        avg_unit_price, avg_discount, order_count, is_zero_filled.
    """

    if valid_df.empty:
        logger.warning("aggregate_daily called with empty DataFrame")
        return pd.DataFrame(columns=OUTPUT_COLUMNS)

    df = valid_df.copy()

    # Ensure correct types
    df["date_"]                 = pd.to_datetime(df["date_"]).dt.date
    df["product_id"]            = df["product_id"].astype(str).str.strip()
    df["city_name"]             = df["city_name"].astype(str).str.strip()
    df["procured_quantity"]     = pd.to_numeric(df["procured_quantity"],    errors="coerce")
    df["unit_selling_price"]    = pd.to_numeric(df["unit_selling_price"],   errors="coerce")
    df["total_discount_amount"] = pd.to_numeric(df["total_discount_amount"], errors="coerce").fillna(0.0)
    df["order_id"]              = df["order_id"].astype(str).str.strip()

    # Revenue per row (used for weighted-average price)
    df["_row_revenue"] = df["procured_quantity"] * df["unit_selling_price"]

    logger.info(
        "aggregate_daily: grouping %d valid rows by (date, product, city)",
        len(df),
    )

    # ------------------------------------------------------------------
    # Aggregation
    # ------------------------------------------------------------------
    agg = (
        df.groupby(GROUP_KEYS, sort=True)
        .agg(
            total_quantity = ("procured_quantity",     "sum"),
            revenue        = ("_row_revenue",           "sum"),
            avg_discount   = ("total_discount_amount",  "mean"),
            order_count    = ("order_id",               _count_distinct),
        )
        .reset_index()
    )

    # Revenue-weighted average unit price: total_revenue / total_quantity
    # Guard against division by zero (should not happen after validation,
    # but defensive coding avoids unexpected NaN propagation).
    agg["avg_unit_price"] = np.where(
        agg["total_quantity"] > 0,
        agg["revenue"] / agg["total_quantity"],
        np.nan,
    )

    # Round financial columns to 4 decimal places
    agg["revenue"]        = agg["revenue"].round(2)
    agg["avg_unit_price"] = agg["avg_unit_price"].round(4)
    agg["avg_discount"]   = agg["avg_discount"].round(4)

    # Cast quantity and order_count to int
    agg["total_quantity"] = agg["total_quantity"].astype(int)
    agg["order_count"]    = agg["order_count"].astype(int)

    # Mark as real (non-zero-filled) rows
    agg["is_zero_filled"] = False

    logger.info(
        "aggregate_daily: produced %d aggregated rows", len(agg)
    )

    # ------------------------------------------------------------------
    # Optional: zero-fill missing dates
    # ------------------------------------------------------------------
    if fill_missing_dates:
        agg = _zero_fill_dates(agg)
        logger.info(
            "aggregate_daily: after zero-fill → %d rows", len(agg)
        )

    # ------------------------------------------------------------------
    # Final column order
    # ------------------------------------------------------------------
    return agg[OUTPUT_COLUMNS].sort_values(GROUP_KEYS).reset_index(drop=True)


# ---------------------------------------------------------------------------
# Zero-fill helper
# ---------------------------------------------------------------------------

def _zero_fill_dates(agg: pd.DataFrame) -> pd.DataFrame:
    """
    Expand each (product_id, city_name) pair to have one row per calendar
    day within the min/max date range of that product-city combination.

    Missing days are filled with zeros and marked is_zero_filled=True.

    NOTE: Zero-filling is applied within each product-city pair independently,
    not globally. A product that was only active for 10 days will not receive
    zero rows for periods before/after its active window.
    """

    records = []

    for (product_id, city_name), group in agg.groupby(["product_id", "city_name"]):
        # Get the active date range for this product-city pair
        prod_date_min = group["date_"].min()
        prod_date_max = group["date_"].max()
        prod_dates    = set(group["date_"].tolist())

        # Expand to every day in this product-city's active window
        active_range = pd.date_range(
            start=prod_date_min, end=prod_date_max, freq="D"
        ).date

        missing_dates = [d for d in active_range if d not in prod_dates]

        if missing_dates:
            zero_rows = pd.DataFrame({
                "date_":          missing_dates,
                "product_id":     product_id,
                "city_name":      city_name,
                "total_quantity": 0,
                "revenue":        0.0,
                "avg_unit_price": np.nan,
                "avg_discount":   np.nan,
                "order_count":    0,
                "is_zero_filled": True,
            })
            records.append(zero_rows)

    if records:
        zero_df = pd.concat(records, ignore_index=True)
        agg     = pd.concat([agg, zero_df], ignore_index=True)

    return agg.sort_values(GROUP_KEYS).reset_index(drop=True)


# ---------------------------------------------------------------------------
# Helper: COUNT(DISTINCT order_id) for groupby
# ---------------------------------------------------------------------------

def _count_distinct(series: pd.Series) -> int:
    """Return count of distinct non-null, non-placeholder values."""
    return int(
        series[series != "NO_ORDER_ID"].nunique()
    )


# ---------------------------------------------------------------------------
# Summary statistics helper (for GET /api/demand/summary)
# ---------------------------------------------------------------------------

def compute_summary(agg_df: pd.DataFrame) -> dict:
    """
    Compute high-level summary statistics from an aggregated demand DataFrame.

    Parameters
    ----------
    agg_df : pd.DataFrame
        Output of aggregate_daily().

    Returns
    -------
    dict
        Summary statistics suitable for the GET /api/demand/summary endpoint.
    """

    if agg_df.empty:
        return {
            "total_rows":          0,
            "unique_products":     0,
            "unique_cities":       0,
            "date_min":            None,
            "date_max":            None,
            "total_quantity":      0,
            "total_revenue":       0.0,
            "top_products_by_qty": [],
        }

    real_rows = agg_df[~agg_df["is_zero_filled"]]

    top_products = (
        real_rows.groupby("product_id")["total_quantity"]
        .sum()
        .nlargest(10)
        .reset_index()
        .rename(columns={"total_quantity": "total_qty"})
        .to_dict("records")
    )

    return {
        "total_rows":          int(len(real_rows)),
        "unique_products":     int(real_rows["product_id"].nunique()),
        "unique_cities":       int(real_rows["city_name"].nunique()),
        "date_min":            str(real_rows["date_"].min()),
        "date_max":            str(real_rows["date_"].max()),
        "total_quantity":      int(real_rows["total_quantity"].sum()),
        "total_revenue":       float(real_rows["revenue"].sum()),
        "top_products_by_qty": top_products,
    }
