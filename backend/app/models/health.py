"""
Health check-in, assessments, timeline, care plans, and medication models.
"""
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Boolean, Float, Date, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.db.database import Base


class HealthCheckin(Base):
    __tablename__ = "health_checkins"

    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(Integer, ForeignKey("patient_profiles.id"), nullable=False)
    
    # Symptoms (JSON arrays)
    symptoms = Column(JSON, nullable=True)  # ["fever", "cough"]
    symptom_details = Column(JSON, nullable=True)  # {"fever": {"severity": 3, "duration": "2 days"}}
    
    # Quick assessments
    feeling_today = Column(String(50), nullable=True)  # good, okay, bad, terrible
    fever = Column(Boolean, default=False)
    fever_temperature = Column(Float, nullable=True)
    cough = Column(Boolean, default=False)
    breathing_difficulty = Column(Boolean, default=False)
    chest_discomfort = Column(Boolean, default=False)
    headache = Column(Boolean, default=False)
    dizziness = Column(Boolean, default=False)
    weakness = Column(Boolean, default=False)
    pain = Column(Boolean, default=False)
    pain_location = Column(String(255), nullable=True)
    pain_severity = Column(Integer, nullable=True)  # 1-10
    vomiting = Column(Boolean, default=False)
    diarrhea = Column(Boolean, default=False)
    sleep_quality = Column(Integer, nullable=True)  # 1-5
    stress_level = Column(Integer, nullable=True)  # 1-5
    medication_taken = Column(Boolean, default=True)
    new_symptoms_text = Column(Text, nullable=True)
    
    # AI Assessment
    ai_risk_level = Column(String(20), nullable=True)  # low, moderate, high, emergency
    ai_assessment = Column(JSON, nullable=True)
    red_flags_detected = Column(Boolean, default=False)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    patient = relationship("PatientProfile", back_populates="health_checkins")
    assessments = relationship("HealthAssessment", back_populates="checkin")


class HealthAssessment(Base):
    __tablename__ = "health_assessments"

    id = Column(Integer, primary_key=True, index=True)
    checkin_id = Column(Integer, ForeignKey("health_checkins.id"), nullable=False)
    patient_id = Column(Integer, ForeignKey("patient_profiles.id"), nullable=False)
    
    # AI Screening results
    possible_concerns = Column(JSON, nullable=True)  # [{"concern": "...", "reason": "...", "confidence": "..."}]
    urgency_level = Column(String(20), nullable=True)  # low, moderate, high, emergency
    reasons = Column(JSON, nullable=True)
    recommended_action = Column(Text, nullable=True)
    warning_signs = Column(JSON, nullable=True)
    
    # Doctor assessment
    doctor_assessment = Column(JSON, nullable=True)
    doctor_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    doctor_notes = Column(Text, nullable=True)
    diagnosis = Column(Text, nullable=True)
    
    # Care route
    care_route = Column(JSON, nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    checkin = relationship("HealthCheckin", back_populates="assessments")


class CarePlan(Base):
    __tablename__ = "care_plans"

    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(Integer, ForeignKey("patient_profiles.id"), nullable=False)
    doctor_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    assessment_id = Column(Integer, ForeignKey("health_assessments.id"), nullable=True)
    
    title = Column(String(255), nullable=True)
    description = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True)
    
    # Care plan details stored as JSON
    medications = Column(JSON, nullable=True)
    follow_up_date = Column(Date, nullable=True)
    lab_tests = Column(JSON, nullable=True)
    doctor_instructions = Column(Text, nullable=True)
    lifestyle_instructions = Column(Text, nullable=True)
    monitoring_schedule = Column(JSON, nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


class MedicationReminder(Base):
    __tablename__ = "medication_reminders"

    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(Integer, ForeignKey("patient_profiles.id"), nullable=False)
    care_plan_id = Column(Integer, ForeignKey("care_plans.id"), nullable=True)
    
    medicine_name = Column(String(255), nullable=False)
    dosage = Column(String(100), nullable=True)
    frequency = Column(String(100), nullable=True)  # morning, afternoon, night, or custom
    time_of_day = Column(String(50), nullable=True)
    
    is_active = Column(Boolean, default=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class MedicationLog(Base):
    __tablename__ = "medication_logs"

    id = Column(Integer, primary_key=True, index=True)
    reminder_id = Column(Integer, ForeignKey("medication_reminders.id"), nullable=False)
    patient_id = Column(Integer, ForeignKey("patient_profiles.id"), nullable=False)
    
    status = Column(String(20), nullable=False)  # taken, skipped, missed
    logged_at = Column(DateTime(timezone=True), server_default=func.now())


class Appointment(Base):
    __tablename__ = "appointments"

    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(Integer, ForeignKey("patient_profiles.id"), nullable=False)
    doctor_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    facility_id = Column(Integer, ForeignKey("healthcare_facilities.id"), nullable=True)
    
    appointment_date = Column(DateTime(timezone=True), nullable=False)
    reason = Column(Text, nullable=True)
    notes = Column(Text, nullable=True)
    status = Column(String(20), default="scheduled")  # scheduled, completed, cancelled, missed
    is_follow_up = Column(Boolean, default=False)
    related_care_plan_id = Column(Integer, ForeignKey("care_plans.id"), nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
