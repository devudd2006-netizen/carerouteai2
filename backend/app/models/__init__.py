"""
Models package - import all models for Alembic discovery.
"""
from app.models.user import User, UserRole
from app.models.patient import PatientProfile, EmergencyContact, DoctorProfile
from app.models.health import (
    HealthCheckin, HealthAssessment, CarePlan,
    MedicationReminder, MedicationLog, Appointment
)
from app.models.document import MedicalDocument, Prescription, PrescriptionItem
from app.models.facility import HealthcareFacility
from app.models.community import Community, CommunityHealthSignal, CommunityPriorityScore, MedicalCampRecommendation
from app.models.emergency import EmergencyEvent, EmergencyHealthCard

__all__ = [
    "User", "UserRole",
    "PatientProfile", "EmergencyContact", "DoctorProfile",
    "HealthCheckin", "HealthAssessment", "CarePlan",
    "MedicationReminder", "MedicationLog", "Appointment",
    "MedicalDocument", "Prescription", "PrescriptionItem",
    "HealthcareFacility",
    "Community", "CommunityHealthSignal", "CommunityPriorityScore", "MedicalCampRecommendation",
    "EmergencyEvent", "EmergencyHealthCard",
]
