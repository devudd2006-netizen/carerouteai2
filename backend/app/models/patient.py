"""
Patient profile and health-related models.
"""
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Boolean, Date, Float
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.db.database import Base


class PatientProfile(Base):
    __tablename__ = "patient_profiles"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False)
    date_of_birth = Column(Date, nullable=True)
    gender = Column(String(20), nullable=True)
    blood_group = Column(String(10), nullable=True)
    address = Column(Text, nullable=True)
    village = Column(String(255), nullable=True)
    district = Column(String(255), nullable=True)
    state = Column(String(255), nullable=True)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    preferred_language = Column(String(20), default="en")
    allergies = Column(Text, nullable=True)  # JSON array
    chronic_conditions = Column(Text, nullable=True)  # JSON array
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    user = relationship("User", backref="patient_profile")
    emergency_contacts = relationship("EmergencyContact", back_populates="patient")
    health_checkins = relationship("HealthCheckin", back_populates="patient")
    medical_documents = relationship("MedicalDocument", back_populates="patient")


class EmergencyContact(Base):
    __tablename__ = "emergency_contacts"

    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(Integer, ForeignKey("patient_profiles.id"), nullable=False)
    name = Column(String(255), nullable=False)
    relationship_type = Column(String(100), nullable=True)
    phone = Column(String(20), nullable=False)
    is_primary = Column(Boolean, default=False)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    patient = relationship("PatientProfile", back_populates="emergency_contacts")


class DoctorProfile(Base):
    __tablename__ = "doctor_profiles"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False)
    specialization = Column(String(255), nullable=True)
    license_number = Column(String(100), nullable=True)
    hospital_name = Column(String(255), nullable=True)
    facility_id = Column(Integer, ForeignKey("healthcare_facilities.id"), nullable=True)
    experience_years = Column(Integer, nullable=True)
    bio = Column(Text, nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    user = relationship("User", backref="doctor_profile")
