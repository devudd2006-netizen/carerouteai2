"""
Health check-in, screening, and timeline routes.
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import desc
from typing import Optional

from app.db.database import get_db
from app.models.user import User
from app.models.patient import PatientProfile
from app.models.health import HealthCheckin, HealthAssessment
from app.schemas.health import (
    HealthCheckinCreate, HealthCheckinResponse,
    HealthAssessmentResponse, CareRouteResponse,
)
from app.services.screening_service import perform_screening
from app.services.care_route_service import generate_care_route
from app.core.auth import get_current_user_id

router = APIRouter(prefix="/api/health", tags=["Health"])


def _get_patient_profile(user_id: int, db: Session) -> PatientProfile:
    profile = db.query(PatientProfile).filter(PatientProfile.user_id == user_id).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Patient profile not found")
    return profile


@router.post("/checkin", response_model=dict)
async def create_checkin(
    data: HealthCheckinCreate,
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """Submit a health check-in and get AI screening results."""
    profile = _get_patient_profile(user_id, db)
    
    # Derive the symptoms list server-side so the timeline/analytics always have
    # a reliable symptom array, even if the client does not send one.
    if not data.symptoms:
        data.symptoms = [
            name for name, flag in [
                ("fever", data.fever),
                ("cough", data.cough),
                ("breathing_difficulty", data.breathing_difficulty),
                ("chest_discomfort", data.chest_discomfort),
                ("headache", data.headache),
                ("dizziness", data.dizziness),
                ("weakness", data.weakness),
                ("pain", data.pain),
                ("vomiting", data.vomiting),
                ("diarrhea", data.diarrhea),
            ] if flag
        ] or None
    
    # Create checkin
    checkin = HealthCheckin(
        patient_id=profile.id,
        feeling_today=data.feeling_today,
        fever=data.fever,
        fever_temperature=data.fever_temperature,
        cough=data.cough,
        breathing_difficulty=data.breathing_difficulty,
        chest_discomfort=data.chest_discomfort,
        headache=data.headache,
        dizziness=data.dizziness,
        weakness=data.weakness,
        pain=data.pain,
        pain_location=data.pain_location,
        pain_severity=data.pain_severity,
        vomiting=data.vomiting,
        diarrhea=data.diarrhea,
        sleep_quality=data.sleep_quality,
        stress_level=data.stress_level,
        medication_taken=data.medication_taken,
        new_symptoms_text=data.new_symptoms_text,
        symptoms=data.symptoms,
        symptom_details=data.symptom_details,
    )
    db.add(checkin)
    db.flush()
    
    # Perform AI screening
    try:
        screening_result = await perform_screening(db, profile.id, checkin.id)
    except Exception as e:
        screening_result = {
            "urgency_level": "low",
            "possible_concerns": [],
            "recommended_action": "Screening temporarily unavailable. Please consult a healthcare professional if concerned.",
            "warning_signs": [],
            "care_route": {},
            "red_flags_detected": False,
            "ai_service_used": "error_fallback",
            "error": str(e)[:200],
        }
    
    db.commit()
    
    return {
        "checkin_id": checkin.id,
        "screening": screening_result,
    }


@router.get("/checkins", response_model=list[HealthCheckinResponse])
def get_checkins(
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """Get user's health check-in history."""
    profile = _get_patient_profile(user_id, db)
    
    checkins = db.query(HealthCheckin).filter(
        HealthCheckin.patient_id == profile.id
    ).order_by(desc(HealthCheckin.created_at)).limit(50).all()
    
    return checkins


@router.get("/checkins/{checkin_id}")
def get_checkin(
    checkin_id: int,
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """Get a specific health check-in."""
    profile = _get_patient_profile(user_id, db)
    
    checkin = db.query(HealthCheckin).filter(
        HealthCheckin.id == checkin_id,
        HealthCheckin.patient_id == profile.id,
    ).first()
    if not checkin:
        raise HTTPException(status_code=404, detail="Check-in not found")
    
    assessment = db.query(HealthAssessment).filter(
        HealthAssessment.checkin_id == checkin_id
    ).first()
    
    return {
        "checkin": checkin,
        "assessment": assessment,
    }


@router.get("/timeline")
def get_health_timeline(
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """Get chronological health timeline."""
    profile = _get_patient_profile(user_id, db)
    
    checkins = db.query(HealthCheckin).filter(
        HealthCheckin.patient_id == profile.id
    ).order_by(desc(HealthCheckin.created_at)).limit(30).all()
    
    timeline = []
    for c in checkins:
        entry = {
            "type": "health_checkin",
            "date": str(c.created_at) if c.created_at else None,
            "data": {
                "id": c.id,
                "feeling_today": c.feeling_today,
                "symptoms": c.symptoms,
                "risk_level": c.ai_risk_level,
                "red_flags": c.red_flags_detected,
            }
        }
        timeline.append(entry)
    
    # Add assessments
    assessments = db.query(HealthAssessment).filter(
        HealthAssessment.patient_id == profile.id
    ).order_by(desc(HealthAssessment.created_at)).limit(20).all()
    
    # Doctor names for assessments with a doctor attached (consultations)
    from app.models.user import User
    doctor_ids = {a.doctor_id for a in assessments if a.doctor_id}
    doctor_names = {
        d.id: d.full_name
        for d in db.query(User).filter(User.id.in_(doctor_ids)).all()
    } if doctor_ids else {}
    
    for a in assessments:
        has_doctor_notes = bool(a.doctor_notes or a.diagnosis)
        entry = {
            "type": "assessment",
            "date": str(a.created_at) if a.created_at else None,
            "data": {
                "id": a.id,
                "urgency_level": a.urgency_level,
                "possible_concerns": a.possible_concerns,
                "recommended_action": a.recommended_action,
                "diagnosis": a.diagnosis,
                "doctor_notes": a.doctor_notes,
                "doctor_name": doctor_names.get(a.doctor_id),
                "is_doctor_consultation": has_doctor_notes,
            }
        }
        timeline.append(entry)
    
    # Sort by date descending
    timeline.sort(key=lambda x: x["date"] or "", reverse=True)
    
    return {"timeline": timeline, "count": len(timeline)}


@router.get("/trends")
def get_health_trends(
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """Get aggregated health trends from recent check-ins.

    Returns per-check-in series (oldest first) for charting, plus totals of the
    most common symptoms. Aggregated from the patient's own data only.
    """
    profile = _get_patient_profile(user_id, db)

    checkins = db.query(HealthCheckin).filter(
        HealthCheckin.patient_id == profile.id
    ).order_by(HealthCheckin.created_at).limit(30).all()

    series = []
    symptom_counts: dict = {}
    for c in checkins:
        symptoms = c.symptoms or []
        for s in symptoms:
            symptom_counts[s] = symptom_counts.get(s, 0) + 1
        series.append({
            "date": str(c.created_at.date()) if c.created_at else None,
            "feeling_today": c.feeling_today,
            "risk_level": c.ai_risk_level or "low",
            "symptom_count": len(symptoms),
            "sleep_quality": c.sleep_quality,
            "stress_level": c.stress_level,
            "pain_severity": c.pain_severity,
        })

    top_symptoms = [
        {"symptom": s, "count": n}
        for s, n in sorted(symptom_counts.items(), key=lambda kv: kv[1], reverse=True)[:8]
    ]

    feeling_counts: dict = {}
    risk_counts: dict = {"low": 0, "moderate": 0, "high": 0, "emergency": 0}
    for c in checkins:
        if c.feeling_today:
            feeling_counts[c.feeling_today] = feeling_counts.get(c.feeling_today, 0) + 1
        risk = c.ai_risk_level or "low"
        risk_counts[risk] = risk_counts.get(risk, 0) + 1

    return {
        "series": series,
        "top_symptoms": top_symptoms,
        "feeling_counts": feeling_counts,
        "risk_counts": risk_counts,
        "total_checkins": len(checkins),
    }


@router.get("/assessments", response_model=list[HealthAssessmentResponse])
def get_assessments(
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """Get health assessments."""
    profile = _get_patient_profile(user_id, db)
    
    assessments = db.query(HealthAssessment).filter(
        HealthAssessment.patient_id == profile.id
    ).order_by(desc(HealthAssessment.created_at)).limit(20).all()
    
    return assessments


@router.post("/screen", response_model=dict)
async def screen_symptoms(
    data: dict,
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """Screen symptoms without creating a check-in (for quick screening)."""
    symptoms = data.get("symptoms", data)
    
    from app.services.ai_service import ai_health_screening
    from app.services.red_flag_engine import evaluate_red_flags
    
    # Red-flag check
    is_emergency, red_flags, guidance = evaluate_red_flags(symptoms)
    
    # AI screening
    result = await ai_health_screening(symptoms)
    
    if is_emergency:
        result["urgency_level"] = "emergency"
    
    result["red_flags_detected"] = is_emergency
    result["red_flags"] = red_flags
    result["emergency_guidance"] = guidance if is_emergency else None
    
    return result


@router.post("/care-route")
async def get_care_route(
    data: dict,
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """Get care route recommendation."""
    result = await generate_care_route(
        db=db,
        urgency_level=data.get("urgency_level", "moderate"),
        symptoms=data.get("symptoms", {}),
        patient_lat=data.get("latitude"),
        patient_lon=data.get("longitude"),
    )
    return result
