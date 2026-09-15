"""
Emergency event and health card models.
"""
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Boolean, JSON, Float
from sqlalchemy.sql import func

from app.db.database import Base


class EmergencyEvent(Base):
    __tablename__ = "emergency_events"

    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(Integer, ForeignKey("patient_profiles.id"), nullable=False)
    
    trigger_checkin_id = Column(Integer, ForeignKey("health_checkins.id"), nullable=True)
    symptoms = Column(JSON, nullable=True)
    red_flags = Column(JSON, nullable=True)
    
    status = Column(String(50), default="detected")  # detected, acknowledged, in_progress, resolved
    guidance = Column(Text, nullable=True)
    recommended_facility_id = Column(Integer, ForeignKey("healthcare_facilities.id"), nullable=True)
    recommended_facility_name = Column(String(255), nullable=True)
    
    location_latitude = Column(Float, nullable=True)
    location_longitude = Column(Float, nullable=True)
    
    is_demo = Column(Boolean, default=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class EmergencyHealthCard(Base):
    __tablename__ = "emergency_health_cards"

    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(Integer, ForeignKey("patient_profiles.id"), nullable=False)
    
    patient_name = Column(String(255), nullable=True)
    age = Column(Integer, nullable=True)
    blood_group = Column(String(10), nullable=True)
    allergies = Column(JSON, nullable=True)
    medical_conditions = Column(JSON, nullable=True)
    current_medications = Column(JSON, nullable=True)
    current_symptoms = Column(JSON, nullable=True)
    recent_health_info = Column(Text, nullable=True)
    emergency_contact_name = Column(String(255), nullable=True)
    emergency_contact_phone = Column(String(20), nullable=True)
    current_location = Column(Text, nullable=True)
    
    share_token = Column(String(100), unique=True, nullable=True)
    is_valid = Column(Boolean, default=True)
    expires_at = Column(DateTime(timezone=True), nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
