from sqlalchemy import Column, BigInteger, Integer, String, Float, Date, DateTime, ForeignKey, Index
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from backend.db.session import Base

class SalesTransaction(Base):
    __tablename__ = "sales"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    upload_id = Column(Integer, ForeignKey("upload_jobs.id", ondelete="SET NULL"), nullable=True, index=True)
    date_ = Column(Date, nullable=False, index=True)
    city_name = Column(String(100), nullable=True, index=True)
    order_id = Column(String(100), nullable=True, index=True)
    cart_id = Column(String(100), nullable=True)
    dim_customer_key = Column(String(100), nullable=True)
    procured_quantity = Column(Float, nullable=False, default=1.0)
    unit_selling_price = Column(Float, nullable=False)
    total_discount_amount = Column(Float, nullable=False, default=0.0)
    product_id = Column(BigInteger, ForeignKey("products.product_id", ondelete="CASCADE"), nullable=False, index=True)
    total_weighted_landing_price = Column(Float, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    product = relationship("Product", back_populates="sales_transactions")
    upload_job = relationship("UploadJob", back_populates="sales_transactions")

    __table_args__ = (
        Index("idx_sales_date_product", "date_", "product_id"),
        Index("idx_sales_city_date", "city_name", "date_"),
    )
