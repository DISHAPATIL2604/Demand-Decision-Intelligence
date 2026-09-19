from sqlalchemy import Column, BigInteger, Integer, String, Float, Boolean, Date, DateTime, ForeignKey, UniqueConstraint, Index
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from backend.db.session import Base

class InventoryState(Base):
    __tablename__ = "inventory"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    product_id = Column(BigInteger, ForeignKey("products.product_id", ondelete="CASCADE"), nullable=False, index=True)
    city_name = Column(String(100), nullable=False, default="ALL", index=True)
    snapshot_date = Column(Date, nullable=False, index=True)
    opening_stock = Column(Float, nullable=False, default=0.0)
    stock_received = Column(Float, nullable=False, default=0.0)
    sales_quantity = Column(Float, nullable=False, default=0.0)
    closing_stock = Column(Float, nullable=False, default=0.0)
    is_simulated = Column(Boolean, nullable=False, default=True)  # Clearly labels model-derived vs real inventory
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    product = relationship("Product", back_populates="inventory_states")

    __table_args__ = (
        UniqueConstraint("product_id", "city_name", "snapshot_date", name="uq_inventory_product_city_date"),
        Index("idx_inventory_product_date", "product_id", "snapshot_date"),
    )

class InventoryRecommendation(Base):
    __tablename__ = "inventory_recommendations"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    product_id = Column(BigInteger, ForeignKey("products.product_id", ondelete="CASCADE"), nullable=False, index=True)
    city_name = Column(String(100), nullable=False, default="ALL", index=True)
    calculation_date = Column(Date, nullable=False, index=True)
    current_stock = Column(Float, nullable=False, default=0.0)
    avg_daily_demand = Column(Float, nullable=False, default=0.0)
    lead_time_days = Column(Integer, nullable=False, default=3)
    safety_stock = Column(Float, nullable=False, default=0.0)
    reorder_point = Column(Float, nullable=False, default=0.0)
    recommended_order_qty = Column(Float, nullable=False, default=0.0)
    risk_status = Column(String(50), nullable=False, default="OPTIMAL", index=True)  # CRITICAL_STOCKOUT, REORDER_RECOMMENDED, OVERSTOCK, OPTIMAL
    priority = Column(String(20), nullable=False, default="MEDIUM")  # HIGH, MEDIUM, LOW
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    product = relationship("Product", back_populates="inventory_recommendations")

    __table_args__ = (
        Index("idx_inv_rec_product_date", "product_id", "calculation_date"),
        Index("idx_inv_rec_risk", "risk_status", "priority"),
    )
