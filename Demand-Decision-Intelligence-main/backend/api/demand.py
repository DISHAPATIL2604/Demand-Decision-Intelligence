"""
backend/api/demand.py
----------------------
FastAPI router for the Daily Demand Aggregation feature.

Endpoints
---------
POST /api/demand/aggregate
    Upload a CSV/Excel sales file.
    → Validate → handle missing values → aggregate daily demand → store in DB.
    Returns a full validation report and aggregation summary.

GET /api/demand/daily
    Query aggregated daily demand rows from the database.
    Supports filtering by product_id, city_name, date range, job_id.
    Supports pagination.

GET /api/demand/summary
    High-level summary statistics (total qty, revenue, top products, date range).
    Optionally scoped to a specific upload_job_id.

Design notes:
  - The full validate → aggregate → persist pipeline runs synchronously.
    For very large files this would move to a background task; for MVP
    synchronous is acceptable and simpler to debug.
  - Raw file bytes are never written to disk; they are parsed in-memory.
  - The ML team can query GET /api/demand/daily directly or read the
    daily_product_demand table via SQLAlchemy / psycopg2.
"""

from __future__ import annotations

import logging
from datetime import date, datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status
from sqlalchemy.orm import Session

from backend.db.session import get_db
from backend.db.models import DailyProductDemand, UploadJob
from backend.schemas.demand import (
    AggregateResponse,
    DailyDemandListResponse,
    DailyDemandRow,
    DateCoverage,
    DemandSummaryResponse,
    OptionalFillSummary,
    RejectionReasonBreakdown,
    TopProductEntry,
    ValidationReport,
)
from backend.services.upload_validator import parse_uploaded_file, validate_and_clean
from backend.services.demand_aggregator import aggregate_daily, compute_summary

logger = logging.getLogger(__name__)

router = APIRouter()

# Maximum file size accepted: 100 MB
MAX_FILE_SIZE_BYTES = 100 * 1024 * 1024


# ---------------------------------------------------------------------------
# POST /api/demand/aggregate
# ---------------------------------------------------------------------------

@router.post(
    "/aggregate",
    response_model=AggregateResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Upload sales file and aggregate daily demand",
    description=(
        "Upload a CSV or Excel (.xlsx/.xls) sales file. "
        "The backend validates required columns, handles safe missing-value fills, "
        "rejects records that cannot be safely used, and aggregates valid records "
        "to daily product demand (grouped by date × product_id × city_name). "
        "Returns a full validation report and the aggregation result."
    ),
)
async def aggregate_uploaded_file(
    file: UploadFile = File(..., description="CSV or Excel sales file"),
    fill_missing_dates: bool = Query(
        False,
        description=(
            "If true, expand each (product_id, city_name) pair to a continuous "
            "date range and fill missing days with zero demand. "
            "Enable only when the ML team needs a continuous time series."
        ),
    ),
    db: Session = Depends(get_db),
) -> AggregateResponse:
    """
    Full pipeline: parse → validate → aggregate → persist.
    """

    # ------------------------------------------------------------------
    # 1. Read file bytes
    # ------------------------------------------------------------------
    file_bytes = await file.read()
    file_size  = len(file_bytes)

    if file_size == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uploaded file is empty.",
        )
    if file_size > MAX_FILE_SIZE_BYTES:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File exceeds maximum allowed size of {MAX_FILE_SIZE_BYTES // 1024 // 1024} MB.",
        )

    filename = file.filename or "upload"
    logger.info("Received upload: %s (%d bytes)", filename, file_size)

    # ------------------------------------------------------------------
    # 2. Create UploadJob (status=validating)
    # ------------------------------------------------------------------
    job = UploadJob(
        original_filename = filename,
        file_size_bytes   = file_size,
        status            = "validating",
    )
    db.add(job)
    db.commit()
    db.refresh(job)
    logger.info("Created UploadJob id=%d", job.id)

    # ------------------------------------------------------------------
    # 3. Parse file
    # ------------------------------------------------------------------
    try:
        raw_df = parse_uploaded_file(file_bytes, filename)
    except ValueError as exc:
        job.status        = "failed"
        job.error_message = str(exc)
        job.finished_at   = datetime.now(timezone.utc)
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        ) from exc

    # ------------------------------------------------------------------
    # 4. Validate and clean
    # ------------------------------------------------------------------
    validation_result = validate_and_clean(raw_df)
    summary           = validation_result.summary

    # Populate job with validation statistics
    job.total_rows_read    = summary.total_rows_read
    job.valid_rows         = summary.valid_rows
    job.rejected_rows      = summary.rejected_rows
    job.duplicate_rows     = summary.duplicate_rows
    job.rows_city_filled   = summary.missing_city_name
    job.rows_discount_filled = summary.missing_discount
    job.rows_order_id_filled = summary.missing_order_id

    if summary.date_min:
        job.upload_date_min = date.fromisoformat(summary.date_min)
    if summary.date_max:
        job.upload_date_max = date.fromisoformat(summary.date_max)

    # Build Pydantic ValidationReport
    validation_report = ValidationReport(
        total_rows_read          = summary.total_rows_read,
        valid_rows               = summary.valid_rows,
        rejected_rows            = summary.rejected_rows,
        duplicate_rows           = summary.duplicate_rows,
        missing_required_columns = summary.missing_required_columns,
        extra_columns_ignored    = summary.extra_columns_ignored,
        rejection_reasons        = RejectionReasonBreakdown(
            **summary.as_dict()["rejection_reasons"]
        ),
        optional_fills           = OptionalFillSummary(
            **summary.as_dict()["optional_fills"]
        ),
        date_coverage            = DateCoverage(
            **summary.as_dict()["date_coverage"]
        ),
        fills_applied            = summary.fills_applied,
        is_acceptable            = summary.is_acceptable(),
    )

    # If no required columns → abort before aggregation
    if summary.missing_required_columns:
        job.status        = "failed"
        job.error_message = f"Missing required columns: {summary.missing_required_columns}"
        job.finished_at   = datetime.now(timezone.utc)
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={
                "message": "Uploaded file is missing required columns.",
                "missing_required_columns": summary.missing_required_columns,
                "validation": validation_report.model_dump(),
            },
        )

    if not summary.is_acceptable():
        job.status        = "failed"
        job.error_message = "No valid rows after validation."
        job.finished_at   = datetime.now(timezone.utc)
        db.commit()
        return AggregateResponse(
            job_id          = job.id,
            status          = "failed",
            filename        = filename,
            aggregated_rows = 0,
            validation      = validation_report,
            message         = (
                f"Upload rejected: 0 valid rows from {summary.total_rows_read} total. "
                "Check validation report for rejection reasons."
            ),
        )

    # ------------------------------------------------------------------
    # 5. Aggregate daily demand
    # ------------------------------------------------------------------
    job.status = "aggregating"
    db.commit()

    agg_df = aggregate_daily(
        valid_df            = validation_result.valid_df,
        fill_missing_dates  = fill_missing_dates,
    )

    # ------------------------------------------------------------------
    # 6. Persist DailyProductDemand rows
    # ------------------------------------------------------------------
    demand_rows = []
    for _, row in agg_df.iterrows():
        demand_rows.append(
            DailyProductDemand(
                upload_job_id  = job.id,
                sale_date      = row["date_"],
                product_id     = str(row["product_id"]),
                city_name      = str(row["city_name"]),
                total_quantity = int(row["total_quantity"]),
                revenue        = float(row["revenue"]),
                avg_unit_price = (
                    float(row["avg_unit_price"])
                    if row["avg_unit_price"] is not None and str(row["avg_unit_price"]) != "nan"
                    else None
                ),
                avg_discount   = (
                    float(row["avg_discount"])
                    if row["avg_discount"] is not None and str(row["avg_discount"]) != "nan"
                    else None
                ),
                order_count    = int(row["order_count"]),
                is_zero_filled = bool(row["is_zero_filled"]),
            )
        )

    # Bulk insert in chunks of 1000 to avoid very large transactions
    chunk_size = 1000
    for i in range(0, len(demand_rows), chunk_size):
        db.bulk_save_objects(demand_rows[i : i + chunk_size])
    db.commit()

    # ------------------------------------------------------------------
    # 7. Finalise job
    # ------------------------------------------------------------------
    job.aggregated_rows = len(demand_rows)
    job.status          = "complete"
    job.finished_at     = datetime.now(timezone.utc)
    db.commit()

    logger.info(
        "UploadJob id=%d complete: valid=%d rejected=%d aggregated=%d",
        job.id,
        summary.valid_rows,
        summary.rejected_rows,
        len(demand_rows),
    )

    return AggregateResponse(
        job_id          = job.id,
        status          = "complete",
        filename        = filename,
        aggregated_rows = len(demand_rows),
        validation      = validation_report,
        message         = (
            f"Successfully aggregated {summary.valid_rows} valid rows "
            f"into {len(demand_rows)} daily demand records. "
            f"{summary.rejected_rows} rows rejected (see validation report)."
        ),
    )


# ---------------------------------------------------------------------------
# GET /api/demand/daily
# ---------------------------------------------------------------------------

@router.get(
    "/daily",
    response_model=DailyDemandListResponse,
    summary="Query aggregated daily demand",
    description=(
        "Return paginated daily product demand records from the database. "
        "Filter by product_id, city_name, date range, or upload_job_id. "
        "The ML team can use this endpoint to retrieve the time-series input "
        "for demand forecasting."
    ),
)
def get_daily_demand(
    product_id:    Optional[str]  = Query(None,  description="Filter by product_id"),
    city_name:     Optional[str]  = Query(None,  description="Filter by city_name"),
    start_date:    Optional[date] = Query(None,  description="Start date (inclusive), format YYYY-MM-DD"),
    end_date:      Optional[date] = Query(None,  description="End date (inclusive), format YYYY-MM-DD"),
    job_id:        Optional[int]  = Query(None,  description="Filter by upload_job_id"),
    exclude_zeros: bool           = Query(False, description="Exclude zero-filled rows"),
    page:          int            = Query(1,     ge=1,    description="Page number"),
    page_size:     int            = Query(100,   ge=1, le=1000, description="Rows per page"),
    db: Session = Depends(get_db),
) -> DailyDemandListResponse:
    """Query daily_product_demand table with optional filters."""

    query = db.query(DailyProductDemand)

    if product_id is not None:
        query = query.filter(DailyProductDemand.product_id == product_id)
    if city_name is not None:
        query = query.filter(DailyProductDemand.city_name == city_name)
    if start_date is not None:
        query = query.filter(DailyProductDemand.sale_date >= start_date)
    if end_date is not None:
        query = query.filter(DailyProductDemand.sale_date <= end_date)
    if job_id is not None:
        query = query.filter(DailyProductDemand.upload_job_id == job_id)
    if exclude_zeros:
        query = query.filter(DailyProductDemand.is_zero_filled == False)  # noqa: E712

    query = query.order_by(
        DailyProductDemand.sale_date,
        DailyProductDemand.product_id,
        DailyProductDemand.city_name,
    )

    total  = query.count()
    offset = (page - 1) * page_size
    rows   = query.offset(offset).limit(page_size).all()

    results = [
        DailyDemandRow(
            id             = row.id,
            sale_date      = row.sale_date,
            product_id     = row.product_id,
            city_name      = row.city_name,
            total_quantity = row.total_quantity,
            revenue        = float(row.revenue),
            avg_unit_price = float(row.avg_unit_price) if row.avg_unit_price is not None else None,
            avg_discount   = float(row.avg_discount)   if row.avg_discount   is not None else None,
            order_count    = row.order_count,
            is_zero_filled = row.is_zero_filled,
            upload_job_id  = row.upload_job_id,
        )
        for row in rows
    ]

    return DailyDemandListResponse(
        total      = total,
        page       = page,
        page_size  = page_size,
        results    = results,
    )


# ---------------------------------------------------------------------------
# GET /api/demand/summary
# ---------------------------------------------------------------------------

@router.get(
    "/summary",
    response_model=DemandSummaryResponse,
    summary="High-level daily demand summary",
    description=(
        "Return summary statistics over the daily_product_demand table: "
        "total quantity, revenue, date range, unique products/cities, "
        "and top 10 products by quantity. "
        "Optionally scope to a specific upload_job_id."
    ),
)
def get_demand_summary(
    job_id: Optional[int] = Query(
        None,
        description="Scope summary to a specific upload_job_id. Omit for all jobs.",
    ),
    db: Session = Depends(get_db),
) -> DemandSummaryResponse:
    """Aggregate summary from daily_product_demand using SQLAlchemy."""

    from sqlalchemy import func, distinct

    # Base query
    q = db.query(DailyProductDemand).filter(
        DailyProductDemand.is_zero_filled == False  # noqa: E712
    )
    if job_id is not None:
        q = q.filter(DailyProductDemand.upload_job_id == job_id)

    # Scalar aggregates
    agg = db.query(
        func.count(DailyProductDemand.id).label("total_rows"),
        func.count(distinct(DailyProductDemand.product_id)).label("unique_products"),
        func.count(distinct(DailyProductDemand.city_name)).label("unique_cities"),
        func.min(DailyProductDemand.sale_date).label("date_min"),
        func.max(DailyProductDemand.sale_date).label("date_max"),
        func.sum(DailyProductDemand.total_quantity).label("total_quantity"),
        func.sum(DailyProductDemand.revenue).label("total_revenue"),
    ).filter(DailyProductDemand.is_zero_filled == False)  # noqa: E712

    if job_id is not None:
        agg = agg.filter(DailyProductDemand.upload_job_id == job_id)

    stats = agg.one()

    # Top 10 products by total quantity
    top_q = (
        db.query(
            DailyProductDemand.product_id,
            func.sum(DailyProductDemand.total_quantity).label("total_qty"),
        )
        .filter(DailyProductDemand.is_zero_filled == False)  # noqa: E712
    )
    if job_id is not None:
        top_q = top_q.filter(DailyProductDemand.upload_job_id == job_id)
    top_q = (
        top_q.group_by(DailyProductDemand.product_id)
        .order_by(func.sum(DailyProductDemand.total_quantity).desc())
        .limit(10)
        .all()
    )

    # Latest job info
    latest_job = (
        db.query(UploadJob)
        .order_by(UploadJob.created_at.desc())
        .first()
    )

    return DemandSummaryResponse(
        total_rows          = int(stats.total_rows or 0),
        unique_products     = int(stats.unique_products or 0),
        unique_cities       = int(stats.unique_cities or 0),
        date_min            = str(stats.date_min)   if stats.date_min   else None,
        date_max            = str(stats.date_max)   if stats.date_max   else None,
        total_quantity      = int(stats.total_quantity or 0),
        total_revenue       = float(stats.total_revenue or 0.0),
        top_products_by_qty = [
            TopProductEntry(product_id=str(r.product_id), total_qty=int(r.total_qty))
            for r in top_q
        ],
        latest_job_id       = latest_job.id       if latest_job else None,
        latest_job_status   = latest_job.status   if latest_job else None,
        latest_job_filename = latest_job.original_filename if latest_job else None,
    )
