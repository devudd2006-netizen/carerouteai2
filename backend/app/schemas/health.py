"""
Health check-in, screening, care plan, and medication schemas.
"""
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import date, datetime


class HealthCheckinCreate(BaseModel):
    feeling_today: Optional[str] = None
    fever: bool = False
    fever_temperature: Optional[float] = None
    cough: bool = False
    breathing_difficulty: bool = False
    chest_discomfort: bool = False
    headache: bool = False
    dizziness: bool = False
    weakness: bool = False
    pain: bool = False
    pain_location: Optional[str] = None
    pain_severity: Optional[int] = None
    vomiting: bool = False
    diarrhea: bool = False
    sleep_quality: Optional[int] = None
    stress_level: Optional[int] = None
    medication_taken: bool = True
    new_symptoms_text: Optional[str] = None
    symptoms: Optional[List[str]] = None
    symptom_details: Optional[Dict[str, Any]] = None


class HealthCheckinResponse(BaseModel):
    id: int
    feeling_today: Optional[str] = None
    fever: bool
    cough: bool
    breathing_difficulty: bool
    chest_discomfort: bool
    headache: bool
    dizziness: bool
    weakness: bool
    pain: bool
    vomiting: bool
    diarrhea: bool
    medication_taken: bool
    new_symptoms_text: Optional[str] = None
    symptoms: Optional[List[str]] = None
    ai_risk_level: Optional[str] = None
    red_flags_detected: bool = False
    created_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class AIScreeningResult(BaseModel):
    possible_concerns: List[Dict[str, Any]] = []
    urgency_level: str = "low"
    reasons: List[str] = []
    recommended_action: str = ""
    warning_signs: List[str] = []
    care_route_recommendation: Optional[str] = None
    ai_service_used: str = "rule_based"


class HealthAssessmentResponse(BaseModel):
    id: int
    checkin_id: int
    possible_concerns: Optional[List[Dict[str, Any]]] = None
    urgency_level: Optional[str] = None
    reasons: Optional[List[str]] = None
    recommended_action: Optional[str] = None
    warning_signs: Optional[List[str]] = None
    doctor_assessment: Optional[Dict[str, Any]] = None
    diagnosis: Optional[str] = None
    doctor_notes: Optional[str] = None
    care_route: Optional[Dict[str, Any]] = None
    created_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class CarePlanCreate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    medications: Optional[List[Dict[str, Any]]] = None
    follow_up_date: Optional[date] = None
    lab_tests: Optional[List[str]] = None
    doctor_instructions: Optional[str] = None
    lifestyle_instructions: Optional[str] = None
    monitoring_schedule: Optional[Dict[str, Any]] = None


class CarePlanResponse(BaseModel):
    id: int
    patient_id: int
    doctor_id: int
    title: Optional[str] = None
    description: Optional[str] = None
    medications: Optional[List[Dict[str, Any]]] = None
    follow_up_date: Optional[date] = None
    lab_tests: Optional[List[str]] = None
    doctor_instructions: Optional[str] = None
    lifestyle_instructions: Optional[str] = None
    monitoring_schedule: Optional[Dict[str, Any]] = None
    is_active: bool
    created_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class MedicationReminderResponse(BaseModel):
    id: int
    medicine_name: str
    dosage: Optional[str] = None
    frequency: Optional[str] = None
    time_of_day: Optional[str] = None
    is_active: bool

    model_config = {"from_attributes": True}


class MedicationLogCreate(BaseModel):
    status: str = Field(..., pattern="^(taken|skipped|missed)$")


class AppointmentCreate(BaseModel):
    doctor_id: Optional[int] = None
    facility_id: Optional[int] = None
    appointment_date: datetime
    reason: Optional[str] = None
    notes: Optional[str] = None
    is_follow_up: bool = False


class AppointmentResponse(BaseModel):
    id: int
    patient_id: int
    doctor_id: Optional[int] = None
    facility_id: Optional[int] = None
    appointment_date: datetime
    reason: Optional[str] = None
    notes: Optional[str] = None
    status: str
    is_follow_up: bool
    doctor_name: Optional[str] = None
    facility_name: Optional[str] = None
    created_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class CareRouteRequest(BaseModel):
    checkin_id: Optional[int] = None
    symptoms: Optional[List[str]] = None
    urgency_level: Optional[str] = None
    patient_latitude: Optional[float] = None
    patient_longitude: Optional[float] = None


class CareRouteResponse(BaseModel):
    what: str = ""
    how_serious: str = ""
    where: str = ""
    what_next: str = ""
    recommended_care_level: str = ""
    recommended_facilities: List[Dict[str, Any]] = []
    urgency_explanation: str = ""
