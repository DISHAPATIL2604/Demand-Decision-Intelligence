"""
backend/services/upload_validator.py
-------------------------------------
Upload Validation Service for user-submitted CSV / Excel sales files.

This module is ONLY responsible for uploaded-data validation and
missing-value handling. It does NOT replicate the ML team's data-cleaning
pipeline (which runs on the pre-cleaned Flipkart dataset offline).

Design principles (from CONVENTIONS.md):
  - Do not silently corrupt or invent data.
  - Investigate the business meaning of missing / zero / negative values.
  - Report rejected records and reasons clearly.
  - Never modify the caller's raw DataFrame in place.

Public API
----------
    result = validate_and_clean(df)

    result.valid_df        – cleaned rows ready for aggregation
    result.rejected_df     – rows that could not be safely handled
    result.summary         – ValidationSummary dataclass
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import List

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Column definitions
# ---------------------------------------------------------------------------

# Required columns — rows missing any of these are rejected
REQUIRED_COLUMNS: List[str] = [
    "date_",
    "product_id",
    "procured_quantity",
    "unit_selling_price",
]

# Optional columns — missing values are safely filled (documented)
OPTIONAL_COLUMNS: List[str] = [
    "city_name",
    "total_discount_amount",
    "order_id",
    "cart_id",
    "dim_customer_key",
    "total_weighted_landing_price",
]

# Fill values for optional columns when missing
OPTIONAL_FILL_VALUES: dict = {
    "city_name":             "Unknown",
    "total_discount_amount": 0.0,
    "order_id":              "NO_ORDER_ID",
}

# All recognised columns (superset of required + optional)
ALL_KNOWN_COLUMNS: List[str] = REQUIRED_COLUMNS + OPTIONAL_COLUMNS


# ---------------------------------------------------------------------------
# Result data structures
# ---------------------------------------------------------------------------

@dataclass
class ValidationSummary:
    """Human-readable summary of the validation run."""

    total_rows_read:    int = 0
    valid_rows:         int = 0
    rejected_rows:      int = 0
    duplicate_rows:     int = 0

    # Per-column missing counts (original, before filling)
    missing_city_name:             int = 0
    missing_discount:              int = 0
    missing_order_id:              int = 0

    # Rejection reason breakdown
    rejected_missing_date:     int = 0
    rejected_bad_date_format:  int = 0
    rejected_missing_product:  int = 0
    rejected_missing_quantity: int = 0
    rejected_bad_quantity:     int = 0   # non-numeric
    rejected_zero_quantity:    int = 0
    rejected_negative_quantity: int = 0
    rejected_missing_price:    int = 0
    rejected_bad_price:        int = 0   # non-numeric
    rejected_negative_price:   int = 0
    rejected_zero_price:       int = 0

    # Date coverage of valid rows
    date_min: str = ""
    date_max: str = ""

    # Optional-column fill summary (non-critical fills)
    fills_applied: List[str] = field(default_factory=list)

    # Schema issues
    missing_required_columns: List[str] = field(default_factory=list)
    extra_columns_ignored:    List[str] = field(default_factory=list)

    def is_acceptable(self) -> bool:
        """True if at least some valid rows exist and schema is intact."""
        return len(self.missing_required_columns) == 0 and self.valid_rows > 0

    def as_dict(self) -> dict:
        return {
            "total_rows_read":    self.total_rows_read,
            "valid_rows":         self.valid_rows,
            "rejected_rows":      self.rejected_rows,
            "duplicate_rows":     self.duplicate_rows,
            "missing_required_columns": self.missing_required_columns,
            "extra_columns_ignored":    self.extra_columns_ignored,
            "rejection_reasons": {
                "missing_date":      self.rejected_missing_date,
                "bad_date_format":   self.rejected_bad_date_format,
                "missing_product":   self.rejected_missing_product,
                "missing_quantity":  self.rejected_missing_quantity,
                "bad_quantity":      self.rejected_bad_quantity,
                "zero_quantity":     self.rejected_zero_quantity,
                "negative_quantity": self.rejected_negative_quantity,
                "missing_price":     self.rejected_missing_price,
                "bad_price":         self.rejected_bad_price,
                "negative_price":    self.rejected_negative_price,
                "zero_price":        self.rejected_zero_price,
            },
            "optional_fills": {
                "city_name_filled":     self.missing_city_name,
                "discount_filled":      self.missing_discount,
                "order_id_filled":      self.missing_order_id,
            },
            "date_coverage": {
                "date_min": self.date_min,
                "date_max": self.date_max,
            },
            "fills_applied": self.fills_applied,
        }


@dataclass
class ValidationResult:
    """Output of validate_and_clean()."""

    valid_df:    pd.DataFrame
    rejected_df: pd.DataFrame
    summary:     ValidationSummary


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------

def validate_and_clean(df: pd.DataFrame) -> ValidationResult:
    """
    Validate and clean an uploaded sales DataFrame.

    Parameters
    ----------
    df : pd.DataFrame
        Raw DataFrame parsed from the user's uploaded CSV/Excel file.
        Must not have been modified by the caller.

    Returns
    -------
    ValidationResult
        .valid_df    – rows that passed all checks (with safe fills applied)
        .rejected_df – rows that were rejected, with a 'rejection_reason' column
        .summary     – ValidationSummary with full statistics
    """

    summary = ValidationSummary()
    df = df.copy()  # never mutate the caller's DataFrame

    summary.total_rows_read = len(df)
    logger.info("validate_and_clean: received %d rows", len(df))

    # ------------------------------------------------------------------
    # Step 1 – Column schema check
    # ------------------------------------------------------------------
    available_cols = set(df.columns.str.strip().str.lower())
    df.columns      = df.columns.str.strip().str.lower()

    missing_required = [c for c in REQUIRED_COLUMNS if c not in df.columns]
    if missing_required:
        summary.missing_required_columns = missing_required
        logger.warning("Missing required columns: %s", missing_required)
        # Return all rows as rejected — cannot proceed without required columns
        df["rejection_reason"] = f"missing_required_columns: {missing_required}"
        return ValidationResult(
            valid_df    = pd.DataFrame(columns=df.columns),
            rejected_df = df,
            summary     = summary,
        )

    # Identify extra (unrecognised) columns — kept but noted
    extra_cols = [c for c in df.columns if c not in ALL_KNOWN_COLUMNS]
    if extra_cols:
        summary.extra_columns_ignored = extra_cols
        logger.debug("Extra columns (ignored for aggregation): %s", extra_cols)

    # Ensure all optional columns exist so downstream code doesn't key-error
    for col in OPTIONAL_COLUMNS:
        if col not in df.columns:
            df[col] = np.nan

    # ------------------------------------------------------------------
    # Step 2 – Duplicate row detection (flag only; rows are kept)
    # ------------------------------------------------------------------
    dup_mask = df.duplicated()
    summary.duplicate_rows = int(dup_mask.sum())
    if summary.duplicate_rows:
        logger.info("Duplicate rows detected: %d (kept)", summary.duplicate_rows)

    # ------------------------------------------------------------------
    # Step 3 – Optional column fills (safe, documented, non-critical)
    # ------------------------------------------------------------------

    # city_name: fill "Unknown" when missing
    # Cast to object first so a string can be assigned into an all-NaN (float64) column.
    df["city_name"] = df["city_name"].astype(object)
    city_null = df["city_name"].isna() | (df["city_name"].astype(str).str.strip() == "")
    summary.missing_city_name = int(city_null.sum())
    if summary.missing_city_name:
        df.loc[city_null, "city_name"] = OPTIONAL_FILL_VALUES["city_name"]
        summary.fills_applied.append(
            f"city_name: {summary.missing_city_name} rows filled with 'Unknown'"
        )

    # total_discount_amount: fill 0.0 when missing (no discount information available)
    disc_null = df["total_discount_amount"].isna()
    summary.missing_discount = int(disc_null.sum())
    if summary.missing_discount:
        df.loc[disc_null, "total_discount_amount"] = OPTIONAL_FILL_VALUES["total_discount_amount"]
        summary.fills_applied.append(
            f"total_discount_amount: {summary.missing_discount} rows filled with 0.0"
        )

    # order_id: fill placeholder when missing (used only for COUNT(DISTINCT order_id))
    # Cast to object first so a string can be assigned into an all-NaN (float64) column.
    df["order_id"] = df["order_id"].astype(object)
    order_null = df["order_id"].isna() | (df["order_id"].astype(str).str.strip() == "")
    summary.missing_order_id = int(order_null.sum())
    if summary.missing_order_id:
        df.loc[order_null, "order_id"] = OPTIONAL_FILL_VALUES["order_id"]
        summary.fills_applied.append(
            f"order_id: {summary.missing_order_id} rows filled with 'NO_ORDER_ID'"
        )

    # ------------------------------------------------------------------
    # Step 4 – Build rejection mask (required field validation)
    # ------------------------------------------------------------------
    reject_mask = pd.Series(False, index=df.index)
    rejection_reasons = pd.Series("", index=df.index)

    # --- date_ ---
    date_null = df["date_"].isna() | (df["date_"].astype(str).str.strip() == "")
    reject_mask |= date_null
    rejection_reasons[date_null] = "missing_date"
    summary.rejected_missing_date = int(date_null.sum())

    # Try parsing dates on non-null rows
    parsed_dates = pd.to_datetime(
        df.loc[~date_null, "date_"], errors="coerce"
    )
    bad_date_mask = pd.Series(False, index=df.index)
    bad_date_idx  = parsed_dates[parsed_dates.isna()].index
    bad_date_mask.loc[bad_date_idx] = True
    reject_mask |= bad_date_mask
    rejection_reasons[bad_date_mask & (rejection_reasons == "")] = "unparseable_date"
    summary.rejected_bad_date_format = int(bad_date_mask.sum())

    # Store parsed dates for valid rows (will be used later)
    df["_parsed_date"] = pd.NaT
    df.loc[~date_null, "_parsed_date"] = parsed_dates

    # --- product_id ---
    prod_null = df["product_id"].isna() | (df["product_id"].astype(str).str.strip() == "")
    reject_mask |= prod_null
    rejection_reasons[prod_null & (rejection_reasons == "")] = "missing_product_id"
    summary.rejected_missing_product = int(prod_null.sum())

    # --- procured_quantity ---
    qty_numeric = pd.to_numeric(df["procured_quantity"], errors="coerce")
    qty_null    = qty_numeric.isna()
    qty_neg     = qty_numeric < 0
    qty_zero    = qty_numeric == 0

    reject_mask |= qty_null
    rejection_reasons[qty_null & (rejection_reasons == "")] = "missing_or_bad_quantity"
    summary.rejected_missing_quantity = int(
        df["procured_quantity"].isna().sum()
    )
    summary.rejected_bad_quantity = int(qty_null.sum()) - summary.rejected_missing_quantity

    reject_mask |= qty_neg
    rejection_reasons[qty_neg & (rejection_reasons == "")] = (
        "negative_quantity (may be return — reject for aggregation)"
    )
    summary.rejected_negative_quantity = int(qty_neg.sum())

    reject_mask |= qty_zero
    rejection_reasons[qty_zero & (rejection_reasons == "")] = "zero_quantity"
    summary.rejected_zero_quantity = int(qty_zero.sum())

    df["_qty_numeric"] = qty_numeric

    # --- unit_selling_price ---
    price_numeric = pd.to_numeric(df["unit_selling_price"], errors="coerce")
    price_null    = price_numeric.isna()
    price_neg     = price_numeric < 0
    price_zero    = price_numeric == 0

    reject_mask |= price_null
    rejection_reasons[price_null & (rejection_reasons == "")] = "missing_or_bad_price"
    summary.rejected_missing_price = int(
        df["unit_selling_price"].isna().sum()
    )
    summary.rejected_bad_price = int(price_null.sum()) - summary.rejected_missing_price

    reject_mask |= price_neg
    rejection_reasons[price_neg & (rejection_reasons == "")] = "negative_price"
    summary.rejected_negative_price = int(price_neg.sum())

    reject_mask |= price_zero
    rejection_reasons[price_zero & (rejection_reasons == "")] = (
        "zero_price (possible data issue — reject to avoid corrupting revenue)"
    )
    summary.rejected_zero_price = int(price_zero.sum())

    df["_price_numeric"] = price_numeric

    # ------------------------------------------------------------------
    # Step 5 – Split valid / rejected
    # ------------------------------------------------------------------
    rejected_df = df[reject_mask].copy()
    rejected_df["rejection_reason"] = rejection_reasons[reject_mask]
    # Drop internal helper columns from rejected export
    rejected_df = rejected_df.drop(
        columns=["_parsed_date", "_qty_numeric", "_price_numeric"],
        errors="ignore",
    )

    valid_df = df[~reject_mask].copy()

    summary.rejected_rows = int(reject_mask.sum())
    summary.valid_rows    = len(valid_df)

    if valid_df.empty:
        logger.warning("No valid rows after validation — all %d rows rejected", summary.total_rows_read)
        return ValidationResult(
            valid_df    = valid_df,
            rejected_df = rejected_df,
            summary     = summary,
        )

    # ------------------------------------------------------------------
    # Step 6 – Finalise valid DataFrame types
    # ------------------------------------------------------------------
    valid_df["date_"]                   = valid_df["_parsed_date"]
    valid_df["procured_quantity"]       = valid_df["_qty_numeric"]
    valid_df["unit_selling_price"]      = valid_df["_price_numeric"]
    valid_df["total_discount_amount"]   = pd.to_numeric(
        valid_df["total_discount_amount"], errors="coerce"
    ).fillna(0.0)
    valid_df["product_id"]              = valid_df["product_id"].astype(str).str.strip()
    valid_df["city_name"]               = valid_df["city_name"].astype(str).str.strip()
    valid_df["order_id"]                = valid_df["order_id"].astype(str).str.strip()

    # Drop internal helper columns
    valid_df = valid_df.drop(
        columns=["_parsed_date", "_qty_numeric", "_price_numeric"],
        errors="ignore",
    )

    # ------------------------------------------------------------------
    # Step 7 – Date coverage of valid rows
    # ------------------------------------------------------------------
    summary.date_min = str(valid_df["date_"].min().date())
    summary.date_max = str(valid_df["date_"].max().date())

    logger.info(
        "validate_and_clean complete: valid=%d rejected=%d date_range=%s→%s",
        summary.valid_rows,
        summary.rejected_rows,
        summary.date_min,
        summary.date_max,
    )

    return ValidationResult(
        valid_df    = valid_df,
        rejected_df = rejected_df,
        summary     = summary,
    )


# ---------------------------------------------------------------------------
# File parsing helper
# ---------------------------------------------------------------------------

def parse_uploaded_file(file_bytes: bytes, filename: str) -> pd.DataFrame:
    """
    Parse an uploaded CSV or Excel file into a raw DataFrame.

    Parameters
    ----------
    file_bytes : bytes
        Raw file bytes from the upload.
    filename : str
        Original filename (used to determine format).

    Returns
    -------
    pd.DataFrame
        Raw DataFrame (no validation applied yet).

    Raises
    ------
    ValueError
        If the file extension is not supported or the file cannot be parsed.
    """
    import io

    name_lower = filename.lower()

    if name_lower.endswith(".csv"):
        try:
            df = pd.read_csv(io.BytesIO(file_bytes), low_memory=False)
        except Exception as exc:
            raise ValueError(f"Could not parse CSV file '{filename}': {exc}") from exc

    elif name_lower.endswith(".xlsx") or name_lower.endswith(".xls"):
        try:
            df = pd.read_excel(io.BytesIO(file_bytes), engine="openpyxl")
        except Exception as exc:
            raise ValueError(
                f"Could not parse Excel file '{filename}': {exc}"
            ) from exc

    else:
        raise ValueError(
            f"Unsupported file type '{filename}'. "
            "Please upload a .csv, .xlsx, or .xls file."
        )

    if df.empty:
        raise ValueError(f"Uploaded file '{filename}' contains no data rows.")

    return df
