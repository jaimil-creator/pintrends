from sqlalchemy import Column, Integer, String, Float, DateTime, Date, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from .db import Base

class Keyword(Base):
    __tablename__ = "keywords"

    id = Column(Integer, primary_key=True, index=True)
    keyword = Column(String, unique=True, index=True)
    last_scraped = Column(DateTime, default=None)

    metrics = relationship("KeywordMetrics", back_populates="keyword_rel")
    pins = relationship("Pin", back_populates="keyword_rel")
    suggestions = relationship("Suggestion", back_populates="parent_keyword_rel")

class KeywordMetrics(Base):
    __tablename__ = "keyword_metrics"

    id = Column(Integer, primary_key=True, index=True)
    keyword_id = Column(Integer, ForeignKey("keywords.id"))
    date = Column(Date, default=datetime.utcnow().date)
    score = Column(Float)
    total_pins = Column(Integer)
    avg_saves = Column(Float)

    keyword_rel = relationship("Keyword", back_populates="metrics")

class Pin(Base):
    __tablename__ = "pins"

    id = Column(Integer, primary_key=True, index=True)
    keyword_id = Column(Integer, ForeignKey("keywords.id"))
    pin_url = Column(String, index=True)
    title = Column(String)
    saves = Column(Integer, default=0)
    created_at = Column(DateTime, nullable=True) 

    keyword_rel = relationship("Keyword", back_populates="pins")

class TrendKeyword(Base):
    __tablename__ = "trend_keywords"

    id = Column(Integer, primary_key=True, index=True)
    keyword = Column(String, index=True)
    detected_at = Column(DateTime, default=datetime.utcnow)
    country = Column(String, default="US")
    trend_type = Column(String, default="growing")
    
    # Filters used to find this trend
    filter_interests = Column(String, nullable=True) # Comma-separated Interest IDs or Names
    filter_ages = Column(String, nullable=True)      # Comma-separated Age Buckets
    filter_genders = Column(String, nullable=True)   # Comma-separated Genders

    # Change Metrics
    weekly_change = Column(String, nullable=True)
    monthly_change = Column(String, nullable=True)
    yearly_change = Column(String, nullable=True)
    
    # JSON Blob for Prediction Graph (TimeSeries)
    prediction_data = Column(String, nullable=True)

class Suggestion(Base):
    __tablename__ = "suggestions"
    
    id = Column(Integer, primary_key=True, index=True)
    parent_keyword_id = Column(Integer, ForeignKey("keywords.id"))
    suggestion = Column(String)
    detected_at = Column(DateTime, default=datetime.utcnow)
    
    parent_keyword_rel = relationship("Keyword", back_populates="suggestions")
