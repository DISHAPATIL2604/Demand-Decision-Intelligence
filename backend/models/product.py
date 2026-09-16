from sqlalchemy import Column, BigInteger, String, Integer, Boolean, DateTime
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from backend.db.session import Base

class Product(Base):
    __tablename__ = "products"

    product_id = Column(BigInteger, primary_key=True, index=True)
    product_name = Column(String(500), nullable=False, index=True)
    unit = Column(String(100), nullable=True)
    product_type = Column(String(100), nullable=True)
    brand_name = Column(String(255), nullable=True, index=True)
    manufacturer_name = Column(String(500), nullable=True)
    l0_category = Column(String(150), nullable=True, index=True)
    l1_category = Column(String(150), nullable=True, index=True)
    l2_category = Column(String(150), nullable=True, index=True)
    l0_category_id = Column(Integer, nullable=True)
    l1_category_id = Column(Integer, nullable=True)
    l2_category_id = Column(Integer, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    sales_transactions = relationship("SalesTransaction", back_populates="product", cascade="all, delete-orphan")
    daily_demands = relationship("DailyProductDemand", back_populates="product", cascade="all, delete-orphan")
    inventory_states = relationship("InventoryState", back_populates="product", cascade="all, delete-orphan")
    inventory_recommendations = relationship("InventoryRecommendation", back_populates="product", cascade="all, delete-orphan")
    forecast_items = relationship("ForecastItem", back_populates="product", cascade="all, delete-orphan")
    anomalies = relationship("AnomalyAlert", back_populates="product", cascade="all, delete-orphan")
