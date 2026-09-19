"""
backend/schemas/demand.py
--------------------------
Pydantic request/response schemas for the Daily Demand Aggregation API.

Convention: snake_case field names, explicit types, no implicit coercion.
"""

from __future__ import annotations

from datetime import date
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Rejection / Validation schemas
# ---------------------------------------------------------------------------

class RejectionReasonBreakdown(BaseModel):
    missing_date:       int = Field(0, description="Rows rejected due to missing date")
    bad_date_format:    int = Field(0, description="Rows rejected due to unparseable date")
    missing_product:    int = Field(0, description="Rows rejected due to missing product_id")
    missing_quantity:   int = Field(0, description="Rows rejected due to missing quantity")
    bad_quantity:       int = Field(0, description="Rows rejected due to non-numeric quantity")
    zero_quantity:      int = Field(0, description="Rows rejected due to zero quantity")
    negative_quantity:  int = Field(0, description="Rows rejected (negative quantity, possible return)")
    missing_price:      int = Field(0, description="Rows rejected due to missing price")
    bad_price:          int = Field(0, description="Rows rejected due to non-numeric price")
    negative_price:     int = Field(0, description="Rows rejected due to negative price")
    zero_price:         int = Field(0, description="Rows rejected due to zero price")


class OptionalFillSummary(BaseModel):
    city_name_filled:  int = Field(0, description="Rows where city_name was filled with 'Unknown'")
    discount_filled:   int = Field(0, description="Rows where discount was filled with 0.0")
    order_id_filled:   int = Field(0, description="Rows where order_id was filled with placeholder")


class DateCoverage(BaseModel):
    date_min: Optional[str] = None
    date_max: Optional[str] = None


class ValidationReport(BaseModel):
    """Full validation report returned with every upload."""

    total_rows_read:          int
    valid_rows:               int
    rejected_rows:            int
    duplicate_rows:           int
    missing_required_columns: List[str] = Field(default_factory=list)
    extra_columns_ignored:    List[str] = Field(default_factory=list)
    rejection_reasons:        RejectionReasonBreakdown
    optional_fills:           OptionalFillSummary
    date_coverage:            DateCoverage
    fills_applied:            List[str] = Field(default_factory=list)
    is_acceptable:            bool = Field(
        description="True if schema is valid and at least one valid row exists"
    )


# ---------------------------------------------------------------------------
# Aggregate endpoint response
# ---------------------------------------------------------------------------

class AggregateResponse(BaseModel):
    """Response returned by POST /api/demand/aggregate."""

    job_id:           int   = Field(description="ID of the created UploadJob")
    status:           str   = Field(description="Job status: complete | failed")
    filename:         str
    aggregated_rows:  int   = Field(description="Number of daily demand rows produced")
    validation:       ValidationReport
    message:          str   = Field(description="Human-readable result summary")


# ---------------------------------------------------------------------------
# Daily demand row schema
# ---------------------------------------------------------------------------

class DailyDemandRow(BaseModel):
    """One row of aggregated daily product demand."""

    id:             Optional[int]   = None
    sale_date:      date            = Field(description="Aggregation date")
    product_id:     str             = Field(description="Product identifier")
    city_name:      str             = Field(description="City name or 'Unknown'")
    total_quantity: int             = Field(description="Sum of procured_quantity")
    revenue:        float           = Field(description="Sum of quantity × unit_selling_price")
    avg_unit_price: Optional[float] = Field(None, description="Revenue-weighted average unit price")
    avg_discount:   Optional[float] = Field(None, description="Average discount amount")
    order_count:    int             = Field(description="Count of distinct order_ids")
    is_zero_filled: bool            = Field(False, description="True if this row fills a date gap")
    upload_job_id:  Optional[int]   = None

    class Config:
        from_attributes = True


# ---------------------------------------------------------------------------
# GET /api/demand/daily query parameters (documented via dependency)
# ---------------------------------------------------------------------------

class DailyDemandListResponse(BaseModel):
    """Paginated list response for GET /api/demand/daily."""

    total:    int
    page:     int
    page_size: int
    results:  List[DailyDemandRow]


# ---------------------------------------------------------------------------
# Summary response
# ---------------------------------------------------------------------------

class TopProductEntry(BaseModel):
    product_id: str
    total_qty:  int


class DemandSummaryResponse(BaseModel):
    """Response for GET /api/demand/summary."""

    total_rows:          int
    unique_products:     int
    unique_cities:       int
    date_min:            Optional[str] = None
    date_max:            Optional[str] = None
    total_quantity:      int
    total_revenue:       float
    top_products_by_qty: List[TopProductEntry] = Field(default_factory=list)

    # Latest job info (optional)
    latest_job_id:       Optional[int]  = None
    latest_job_status:   Optional[str]  = None
    latest_job_filename: Optional[str]  = None
