"""Persistent market-price observations and explicit product mappings."""

from sqlalchemy import Column, BigInteger, Date, DateTime, Float, ForeignKey, Integer, String, Text, UniqueConstraint, Index
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from backend.db.session import Base


class MarketPriceObservation(Base):
    __tablename__ = "market_price_observations"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    source = Column(String(40), nullable=False)
    commodity = Column(String(200), nullable=False)
    variety = Column(String(200), nullable=False, default="")
    market = Column(String(200), nullable=False, default="")
    state = Column(String(100), nullable=False, default="")
    district = Column(String(100), nullable=False, default="")
    price_date = Column(Date, nullable=False)
    min_price = Column(Float)
    max_price = Column(Float)
    modal_price = Column(Float)
    retail_price = Column(Float)
    wholesale_price = Column(Float)
    unit = Column(String(60), nullable=False, default="")
    raw_source_reference = Column(Text)
    fetched_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    __table_args__ = (
        UniqueConstraint("source", "commodity", "variety", "market", "state", "district", "price_date", name="uq_market_price_observation"),
        Index("idx_market_price_commodity_date", "commodity", "price_date"),
        Index("idx_market_price_latest", "source", "commodity", "price_date"),
    )


class ProductCommodityMapping(Base):
    __tablename__ = "product_commodity_mappings"

    id = Column(Integer, primary_key=True, autoincrement=True)
    product_id = Column(BigInteger, ForeignKey("products.product_id", ondelete="CASCADE"), nullable=False, unique=True)
    commodity = Column(String(200), nullable=False)
    mapping_method = Column(String(60), nullable=False, default="controlled_rule")
    mapping_reason = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    product = relationship("Product", back_populates="commodity_mapping")
