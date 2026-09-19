from sqlalchemy import Column, Integer, BigInteger, String, Float, Date, DateTime, ForeignKey, Text, UniqueConstraint, Index
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from backend.db.session import Base

class ForecastRun(Base):
    __tablename__ = "forecast_runs"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    model_name = Column(String(100), nullable=False, index=True)  # Prophet, MovingAverage_7D, Naive
    horizon_days = Column(Integer, nullable=False, default=14)  # 7, 14, 30
    status = Column(String(50), nullable=False, default="RUNNING", index=True)  # RUNNING, COMPLETED, FAILED
    start_date = Column(Date, nullable=True)
    end_date = Column(Date, nullable=True)
    metrics_summary = Column(Text, nullable=True)  # JSON summary of metrics
    created_by_user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    completed_at = Column(DateTime(timezone=True), nullable=True)

    forecast_items = relationship("ForecastItem", back_populates="run", cascade="all, delete-orphan")
    evaluations = relationship("ForecastEvaluation", back_populates="run", cascade="all, delete-orphan")

class ForecastItem(Base):
    __tablename__ = "forecasts"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    run_id = Column(Integer, ForeignKey("forecast_runs.id", ondelete="CASCADE"), nullable=False, index=True)
    product_id = Column(BigInteger, ForeignKey("products.product_id", ondelete="CASCADE"), nullable=False, index=True)
    city_name = Column(String(100), nullable=False, default="ALL", index=True)
    forecast_date = Column(Date, nullable=False, index=True)
    predicted_demand = Column(Float, nullable=False)
    lower_bound = Column(Float, nullable=True)
    upper_bound = Column(Float, nullable=True)
    model_name = Column(String(100), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    run = relationship("ForecastRun", back_populates="forecast_items")
    product = relationship("Product", back_populates="forecast_items")

    __table_args__ = (
        UniqueConstraint("run_id", "product_id", "city_name", "forecast_date", name="uq_forecast_run_product_city_date"),
        Index("idx_forecast_product_date", "product_id", "forecast_date"),
    )

class ForecastEvaluation(Base):
    __tablename__ = "forecast_evaluations"

    id = Column(Integer, primary_key=True, autoincrement=True)
    run_id = Column(Integer, ForeignKey("forecast_runs.id", ondelete="CASCADE"), nullable=False, index=True)
    product_id = Column(BigInteger, ForeignKey("products.product_id", ondelete="CASCADE"), nullable=False, index=True)
    city_name = Column(String(100), nullable=False, default="ALL")
    model_name = Column(String(100), nullable=False)
    mae = Column(Float, nullable=True)
    rmse = Column(Float, nullable=True)
    mape = Column(Float, nullable=True)
    wape = Column(Float, nullable=True)
    evaluation_date = Column(DateTime(timezone=True), server_default=func.now())

    run = relationship("ForecastRun", back_populates="evaluations")
