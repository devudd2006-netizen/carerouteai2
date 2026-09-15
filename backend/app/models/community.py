"""
Community health data models for Community Health Pulse.
"""
from sqlalchemy import Column, Integer, String, Text, DateTime, Float, Boolean, JSON, ForeignKey
from sqlalchemy.sql import func

from app.db.database import Base


class Community(Base):
    __tablename__ = "communities"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    village = Column(String(255), nullable=True)
    district = Column(String(255), nullable=True)
    state = Column(String(255), nullable=True)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    population = Column(Integer, nullable=True)
    
    # Healthcare access metrics
    distance_to_nearest_facility_km = Column(Float, nullable=True)
    nearest_facility_type = Column(String(100), nullable=True)
    has_phc = Column(Boolean, default=False)
    has_chc = Column(Boolean, default=False)
    has_hospital = Column(Boolean, default=False)
    has_pharmacy = Column(Boolean, default=False)
    
    # Vulnerability indicators
    elderly_population_pct = Column(Float, nullable=True)
    children_population_pct = Column(Float, nullable=True)
    pregnant_women_count = Column(Integer, nullable=True)
    accessibility_score = Column(Float, nullable=True)  # 0-1, 1=best
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


class CommunityHealthSignal(Base):
    __tablename__ = "community_health_signals"

    id = Column(Integer, primary_key=True, index=True)
    community_id = Column(Integer, ForeignKey("communities.id"), nullable=False)
    
    signal_type = Column(String(100), nullable=False)  # symptom_cluster, demand_spike, etc.
    symptom_category = Column(String(100), nullable=True)
    report_count = Column(Integer, default=1)
    severity_indicator = Column(Float, nullable=True)  # 0-1
    date_range_start = Column(DateTime(timezone=True), nullable=True)
    date_range_end = Column(DateTime(timezone=True), nullable=True)
    details = Column(JSON, nullable=True)
    
    is_confirmed = Column(Boolean, default=False)
    investigation_needed = Column(Boolean, default=False)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class CommunityPriorityScore(Base):
    __tablename__ = "community_priority_scores"

    id = Column(Integer, primary_key=True, index=True)
    community_id = Column(Integer, ForeignKey("communities.id"), nullable=False)
    
    priority_score = Column(Float, nullable=False)  # 0-100
    priority_level = Column(String(20), nullable=False)  # low, medium, high, critical
    
    # Score components
    distance_score = Column(Float, nullable=True)
    population_vulnerability_score = Column(Float, nullable=True)
    health_demand_score = Column(Float, nullable=True)
    facility_availability_score = Column(Float, nullable=True)
    accessibility_score = Column(Float, nullable=True)
    
    reasons = Column(JSON, nullable=True)
    calculated_at = Column(DateTime(timezone=True), server_default=func.now())


class MedicalCampRecommendation(Base):
    __tablename__ = "medical_camp_recommendations"

    id = Column(Integer, primary_key=True, index=True)
    community_id = Column(Integer, ForeignKey("communities.id"), nullable=False)
    
    recommended_location = Column(String(255), nullable=True)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    priority_score = Column(Float, nullable=True)
    reason = Column(Text, nullable=True)
    population_affected = Column(Integer, nullable=True)
    healthcare_gaps = Column(JSON, nullable=True)
    suggested_services = Column(JSON, nullable=True)
    suggested_duration_days = Column(Integer, nullable=True)
    suggested_route = Column(Text, nullable=True)
    
    is_implemented = Column(Boolean, default=False)
    is_acknowledged = Column(Boolean, default=False)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
