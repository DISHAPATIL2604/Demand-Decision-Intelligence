from sqlalchemy import Column, BigInteger, Integer, String, Float, Date, DateTime, ForeignKey, UniqueConstraint, Index
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from backend.db.session import Base

class DailyProductDemand(Base):
    __tablename__ = "daily_product_demand"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    date_ = Column(Date, nullable=False, index=True)
    product_id = Column(BigInteger, ForeignKey("products.product_id", ondelete="CASCADE"), nullable=False, index=True)
    city_name = Column(String(100), nullable=False, default="ALL", index=True)
    total_quantity = Column(Float, nullable=False, default=0.0)
    total_sales_value = Column(Float, nullable=False, default=0.0)
    total_discount_value = Column(Float, nullable=False, default=0.0)
    avg_unit_price = Column(Float, nullable=True)
    order_count = Column(Integer, nullable=False, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    product = relationship("Product", back_populates="daily_demands")

    __table_args__ = (
        UniqueConstraint("date_", "product_id", "city_name", name="uq_daily_demand_date_product_city"),
        Index("idx_demand_product_date", "product_id", "date_"),
        Index("idx_demand_city_product", "city_name", "product_id"),
    )
