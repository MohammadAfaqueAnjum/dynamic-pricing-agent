from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from database.connection import Base

class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)
    sku = Column(String, unique=True, index=True, nullable=False)
    title = Column(String, nullable=False)
    base_cost = Column(Float, nullable=False)
    current_price = Column(Float, nullable=False)
    min_margin_percent = Column(Float, default=0.15)
    stock_count = Column(Integer, default=10)

    trackers = relationship("CompetitorTracker", back_populates="product")
    logs = relationship("PriceLog", back_populates="product")

class CompetitorTracker(Base):
    __tablename__ = "competitor_trackers"

    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id"))
    competitor_name = Column(String, nullable=False)
    competitor_url = Column(String, nullable=False)
    last_scraped_price = Column(Float, nullable=True)
    in_stock = Column(Boolean, default=True)
    last_checked_at = Column(DateTime, default=datetime.utcnow)

    product = relationship("Product", back_populates="trackers")

class PriceLog(Base):
    __tablename__ = "price_logs"

    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id"))
    old_price = Column(Float, nullable=False)
    suggested_price = Column(Float, nullable=False)
    final_price = Column(Float, nullable=False)
    reasoning = Column(Text, nullable=False)
    status = Column(String, default="APPLIED")
    created_at = Column(DateTime, default=datetime.utcnow)

    product = relationship("Product", back_populates="logs")
