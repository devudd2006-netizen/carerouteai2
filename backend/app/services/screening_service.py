"""
Screening Service - Combines AI screening with red-flag safety engine.

The red-flag engine ALWAYS takes priority. If red flags are detected,
the screening result is elevated to emergency regardless of AI output.
"""
import logging
from typing import Dict, Any, Optional
from sqlalchemy.orm import Session

from app.services.ai_service import ai_health_screening
from app.services.red_flag_engine import evaluate_red_flags
from app.services.care_route_service import generate_care_route
from app.models.health import HealthCheckin, HealthAssessment
from app.models.patient import PatientProfile

logger = logging.getLogger(__name__)


def _build_symptom_dict(checkin) -> Dict[str, Any]:
    """Convert checkin object to symptom dictionary for analysis."""
    return {
        "fever": checkin.fever or False,
        "fever_temperature": checkin.fever_temperature,
        "cough": checkin.cough or False,
        "breathing_difficulty": checkin.breathing_difficulty or False,
        "chest_discomfort": checkin.chest_discomfort or False,
        "headache": checkin.headache or False,
        "dizziness": checkin.dizziness or False,
        "weakness": checkin.weakness or False,
        "pain": checkin.pain or False,
        "pain_location": checkin.pain_location,
        "pain_severity": checkin.pain_severity,  # None means not reported (rules treat unknown as 0)
        "vomiting": checkin.vomiting or False,
        "diarrhea": checkin.diarrhea or False,
        "medication_taken": checkin.medication_taken or False,
        "new_symptoms_text": checkin.new_symptoms_text or "",
    }


async def perform_screening(
    db: Session,
    patient_id: int,
    checkin_id: int,
) -> Dict[str, Any]:
    """
    Perform complete health screening:
    1. Run rule-based red-flag check
    2. Run AI-assisted screening
    3. Merge results (red-flag always wins)
    4. Generate care route
    5. Save assessment
    """
    # Get checkin and patient data
    checkin = db.query(HealthCheckin).filter(HealthCheckin.id == checkin_id).first()
    if not checkin:
        raise ValueError("Health check-in not found")
    
    patient = db.query(PatientProfile).filter(PatientProfile.id == patient_id).first()
    
    # Build symptom dictionary
    symptoms = _build_symptom_dict(checkin)
    
    # Step 1: Red-flag evaluation (ALWAYS runs, deterministic)
    is_emergency, red_flags, emergency_guidance = evaluate_red_flags(symptoms)
    
    # Step 2: AI-assisted screening
    patient_context = {}
    if patient:
        from datetime import date
        age = None
        if patient.date_of_birth:
            age = (date.today() - patient.date_of_birth).days // 365
        patient_context = {
            "age": age,
            "chronic_conditions": patient.chronic_conditions,
            "allergies": patient.allergies,
            "gender": patient.gender,
        }
    
    ai_result = await ai_health_screening(symptoms, patient_context)
    
    # Step 3: Merge - red flags override
    urgency_level = ai_result.get("urgency_level", "low")
    if is_emergency:
        urgency_level = "emergency"
    
    # Update checkin with initial assessment
    checkin.ai_risk_level = urgency_level
    checkin.red_flags_detected = is_emergency
    checkin.ai_assessment = ai_result
    
    # Step 4: Generate care route
    care_route = await generate_care_route(
        db=db,
        urgency_level=urgency_level,
        symptoms=symptoms,
        patient_lat=patient.latitude if patient else None,
        patient_lon=patient.longitude if patient else None,
    )
    
    # Step 5: Create assessment record
    assessment = HealthAssessment(
        checkin_id=checkin_id,
        patient_id=patient_id,
        possible_concerns=ai_result.get("possible_concerns", []),
        urgency_level=urgency_level,
        reasons=ai_result.get("reasons", []),
        recommended_action=ai_result.get("recommended_action", ""),
        warning_signs=ai_result.get("warning_signs", []),
        care_route=care_route,
    )
    db.add(assessment)
    db.commit()
    db.refresh(assessment)
    
    # Build response
    response = {
        "assessment_id": assessment.id,
        "urgency_level": urgency_level,
        "possible_concerns": ai_result.get("possible_concerns", []),
        "reasons": ai_result.get("reasons", []),
        "recommended_action": ai_result.get("recommended_action", ""),
        "warning_signs": ai_result.get("warning_signs", []),
        "care_route": care_route,
        "red_flags_detected": is_emergency,
        "red_flags": red_flags,
        "emergency_guidance": emergency_guidance if is_emergency else None,
        "ai_service_used": ai_result.get("ai_service_used", "unknown"),
    }
    
    # Add emergency-specific info
    if is_emergency:
        response["emergency_alert"] = True
        response["emergency_message"] = (
            "POTENTIAL EMERGENCY DETECTED. "
            "Seek urgent medical attention immediately."
        )
    
    return response
