"""
backend/db/models.py
--------------------
SQLAlchemy ORM models for the Demand & Decision Intelligence System.

Tables created here:
  upload_jobs          – one row per file upload attempt
  sales_records        – validated/cleaned individual transaction rows
  daily_product_demand – aggregated daily demand (the ML team's input)

Convention: snake_case column names (per CONVENTIONS.md).
"""

from datetime import datetime, date, timezone
from sqlalchemy import (
    Column, Integer, BigInteger, String, Numeric, Date, DateTime,
    Boolean, Text, ForeignKey, UniqueConstraint, Index,
)
from sqlalchemy.orm import relationship
from backend.db.session import Base


# ---------------------------------------------------------------------------
# UploadJob
# ---------------------------------------------------------------------------

class UploadJob(Base):
    """
    Tracks every file upload attempt.

    One row is created when a user submits a file to POST /api/demand/aggregate.
    Status progresses: pending → validating → aggregating → complete | failed.
    """

    __tablename__ = "upload_jobs"

    id = Column(Integer, primary_key=True, index=True)

    # File metadata
    original_filename = Column(String(255), nullable=False)
    file_size_bytes   = Column(BigInteger, nullable=True)

    # Row-level accounting
    total_rows_read    = Column(Integer, default=0, nullable=False)
    valid_rows         = Column(Integer, default=0, nullable=False)
    rejected_rows      = Column(Integer, default=0, nullable=False)
    duplicate_rows     = Column(Integer, default=0, nullable=False)

    # Missing-value fills (non-critical columns that were safely filled)
    rows_city_filled     = Column(Integer, default=0, nullable=False)
    rows_discount_filled = Column(Integer, default=0, nullable=False)
    rows_order_id_filled = Column(Integer, default=0, nullable=False)

    # Date coverage of the uploaded file
    upload_date_min = Column(Date, nullable=True)
    upload_date_max = Column(Date, nullable=True)

    # Job status
    status = Column(
        String(32),
        default="pending",
        nullable=False,
        comment="pending | validating | aggregating | complete | failed",
    )
    error_message = Column(Text, nullable=True)

    # Aggregation summary
    aggregated_rows = Column(Integer, default=0, nullable=False)

    # Timestamps
    created_at  = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    finished_at = Column(DateTime, nullable=True)

    # Relationships
    sales_records        = relationship("SalesRecord",        back_populates="upload_job", lazy="dynamic")
    daily_demand_records = relationship("DailyProductDemand", back_populates="upload_job", lazy="dynamic")

    def __repr__(self) -> str:
        return (
            f"<UploadJob id={self.id} file={self.original_filename!r} "
            f"status={self.status!r}>"
        )


# ---------------------------------------------------------------------------
# SalesRecord
# ---------------------------------------------------------------------------

class SalesRecord(Base):
    """
    Stores individual validated/cleaned transaction rows after upload.

    These are the 'cleaned' rows that passed all mandatory checks.
    The demand aggregator reads from this table (or directly from the
    in-memory DataFrame if called in the same request pipeline).

    NOTE: This table is intentionally kept lean — it mirrors the raw
    column set exactly. The daily_product_demand table is the aggregated
    output for downstream ML use.
    """

    __tablename__ = "sales_records"

    id = Column(BigInteger, primary_key=True, index=True)

    upload_job_id = Column(
        Integer,
        ForeignKey("upload_jobs.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Core transaction fields (required — rows without these are rejected)
    sale_date           = Column(Date,          nullable=False)
    product_id          = Column(String(64),    nullable=False)
    procured_quantity   = Column(Numeric(12, 4), nullable=False)
    unit_selling_price  = Column(Numeric(12, 4), nullable=False)

    # Derived / optional fields (safely filled when missing)
    city_name              = Column(String(128), nullable=False, default="Unknown")
    total_discount_amount  = Column(Numeric(12, 4), nullable=False, default=0.0)
    order_id               = Column(String(64),  nullable=True)

    # Extra columns from the Flipkart dataset schema (stored if present)
    cart_id                      = Column(String(64),  nullable=True)
    dim_customer_key             = Column(String(64),  nullable=True)
    total_weighted_landing_price = Column(Numeric(14, 4), nullable=True)

    # Relationship
    upload_job = relationship("UploadJob", back_populates="sales_records")

    __table_args__ = (
        Index("ix_sales_records_sale_date_product", "sale_date", "product_id"),
        # NOTE: upload_job_id index is covered by index=True on the column above.
    )

    def __repr__(self) -> str:
        return (
            f"<SalesRecord id={self.id} date={self.sale_date} "
            f"product={self.product_id} qty={self.procured_quantity}>"
        )


# ---------------------------------------------------------------------------
# DailyProductDemand
# ---------------------------------------------------------------------------

class DailyProductDemand(Base):
    """
    Aggregated daily demand output — the primary table for ML forecasting.

    One row per (sale_date, product_id, city_name) combination within
    a given upload job.

    Column alignment with the ML team's existing CSV:
      date_          → sale_date
      product_id     → product_id
      city_name      → city_name
      daily_quantity → total_quantity
      daily_revenue  → revenue
      order_count    → order_count

    Additional columns added for ML feature use:
      avg_unit_price – revenue-weighted average unit price
      avg_discount   – average discount per transaction in the group
      is_zero_filled – True if this row was synthesised for a date gap
    """

    __tablename__ = "upload_daily_demand"

    id = Column(Integer, primary_key=True, index=True)

    upload_job_id = Column(
        Integer,
        ForeignKey("upload_jobs.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Aggregation key (date + product + city)
    sale_date   = Column(Date,       nullable=False)
    product_id  = Column(String(64), nullable=False)
    city_name   = Column(String(128), nullable=False)

    # Aggregated demand metrics
    total_quantity = Column(Integer,      nullable=False, default=0)
    revenue        = Column(Numeric(16, 2), nullable=False, default=0)
    avg_unit_price = Column(Numeric(12, 4), nullable=True)   # revenue-weighted avg
    avg_discount   = Column(Numeric(12, 4), nullable=True)   # simple average
    order_count    = Column(Integer,      nullable=False, default=0)

    # Zero-fill flag: True when this row fills a date gap (no actual sales)
    is_zero_filled = Column(Boolean, default=False, nullable=False)

    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    # Relationship
    upload_job = relationship("UploadJob", back_populates="daily_demand_records")

    __table_args__ = (
        # Each (date, product, city) is unique within a job
        UniqueConstraint(
            "sale_date", "product_id", "city_name", "upload_job_id",
            name="uq_upload_daily_demand_key",
        ),
        Index("ix_upload_daily_demand_date_product", "sale_date", "product_id"),
        Index("ix_upload_daily_demand_upload_job",   "upload_job_id"),
    )

    def __repr__(self) -> str:
        return (
            f"<DailyProductDemand date={self.sale_date} "
            f"product={self.product_id} city={self.city_name!r} "
            f"qty={self.total_quantity}>"
        )
