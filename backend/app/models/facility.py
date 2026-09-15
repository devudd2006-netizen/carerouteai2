"""
Healthcare facility model.
"""
from sqlalchemy import Column, Integer, String, Text, DateTime, Float, Boolean, JSON
from sqlalchemy.sql import func

from app.db.database import Base


class HealthcareFacility(Base):
    __tablename__ = "healthcare_facilities"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    facility_type = Column(String(100), nullable=False)  # hospital, phc, chc, clinic, pharmacy, diagnostic, emergency
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    address = Column(Text, nullable=True)
    village = Column(String(255), nullable=True)
    district = Column(String(255), nullable=True)
    state = Column(String(255), nullable=True)
    
    services = Column(JSON, nullable=True)  # ["general", "emergency", "surgery", "diagnostics"]
    emergency_available = Column(Boolean, default=False)
    opening_hours = Column(String(255), nullable=True)
    contact_number = Column(String(20), nullable=True)
    accessibility_info = Column(Text, nullable=True)
    
    is_active = Column(Boolean, default=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
