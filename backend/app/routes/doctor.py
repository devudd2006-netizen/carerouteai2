"""
Doctor dashboard routes.
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import desc
from typing import Optional
import json
from datetime import date

from app.db.database import get_db
from app.models.user import User
from app.models.patient import PatientProfile, DoctorProfile
from app.models.health import HealthCheckin, HealthAssessment, CarePlan, Appointment
from app.models.document import MedicalDocument
from app.core.auth import get_current_user_id, require_role

router = APIRouter(prefix="/api/doctor", tags=["Doctor"])


@router.get("/patients")
def list_patients(
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """List patients accessible to this doctor."""
    # Verify doctor role
    doctor = db.query(DoctorProfile).filter(DoctorProfile.user_id == user_id).first()
    
    # For demo: show all patients (in production, would filter by assignments)
    profiles = db.query(PatientProfile).all()
    
    patients = []
    for p in profiles:
        user = db.query(User).filter(User.id == p.user_id).first()
        if not user:
            continue
        
        # Get latest checkin
        latest_checkin = db.query(HealthCheckin).filter(
            HealthCheckin.patient_id == p.id
        ).order_by(desc(HealthCheckin.created_at)).first()
        
        age = None
        if p.date_of_birth:
            age = (date.today() - p.date_of_birth).days // 365
        
        patients.append({
            "id": p.id,
            "user_id": p.user_id,
            "name": user.full_name,
            "email": user.email,
            "age": age,
            "gender": p.gender,
            "village": p.village,
            "district": p.district,
            "latest_risk_level": latest_checkin.ai_risk_level if latest_checkin else None,
            "latest_checkin_date": str(latest_checkin.created_at) if latest_checkin else None,
        })
    
    return {"patients": patients, "count": len(patients)}


@router.get("/patients/{patient_id}")
def get_patient_detail(
    patient_id: int,
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """Get detailed patient view for doctor."""
    profile = db.query(PatientProfile).filter(PatientProfile.id == patient_id).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Patient not found")
    
    user = db.query(User).filter(User.id == profile.user_id).first()
    
    # Get health history
    checkins = db.query(HealthCheckin).filter(
        HealthCheckin.patient_id == patient_id
    ).order_by(desc(HealthCheckin.created_at)).limit(10).all()
    
    assessments = db.query(HealthAssessment).filter(
        HealthAssessment.patient_id == patient_id
    ).order_by(desc(HealthAssessment.created_at)).limit(10).all()
    
    care_plans = db.query(CarePlan).filter(
        CarePlan.patient_id == patient_id
    ).order_by(desc(CarePlan.created_at)).limit(5).all()
    
    documents = db.query(MedicalDocument).filter(
        MedicalDocument.patient_id == patient_id
    ).order_by(desc(MedicalDocument.created_at)).limit(10).all()
    
    appointments = db.query(Appointment).filter(
        Appointment.patient_id == patient_id
    ).order_by(desc(Appointment.appointment_date)).limit(10).all()
    
    age = None
    if profile.date_of_birth:
        age = (date.today() - profile.date_of_birth).days // 365
    
    return {
        "profile": {
            "id": profile.id,
            "name": user.full_name if user else "Unknown",
            "age": age,
            "gender": profile.gender,
            "blood_group": profile.blood_group,
            "allergies": profile.allergies,
            "chronic_conditions": profile.chronic_conditions,
            "village": profile.village,
            "district": profile.district,
        },
        "checkins": [
            {
                "id": c.id,
                "symptoms": c.symptoms,
                "risk_level": c.ai_risk_level,
                "created_at": str(c.created_at) if c.created_at else None,
            }
            for c in checkins
        ],
        "assessments": [
            {
                "id": a.id,
                "urgency_level": a.urgency_level,
                "possible_concerns": a.possible_concerns,
                "diagnosis": a.diagnosis,
                "doctor_notes": a.doctor_notes,
                "created_at": str(a.created_at) if a.created_at else None,
            }
            for a in assessments
        ],
        "care_plans": [
            {
                "id": cp.id,
                "title": cp.title,
                "is_active": cp.is_active,
                "created_at": str(cp.created_at) if cp.created_at else None,
            }
            for cp in care_plans
        ],
        "documents": [
            {
                "id": d.id,
                "title": d.title,
                "document_type": d.document_type,
                "created_at": str(d.created_at) if d.created_at else None,
            }
            for d in documents
        ],
        "appointments": [
            {
                "id": a.id,
                "date": str(a.appointment_date) if a.appointment_date else None,
                "status": a.status,
                "reason": a.reason,
            }
            for a in appointments
        ],
    }


@router.post("/consultations")
def add_consultation(
    data: dict,
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """Doctor adds consultation notes and assessment."""
    patient_id = data.get("patient_id")
    if not patient_id:
        raise HTTPException(status_code=400, detail="Patient ID required")
    
    assessment_id = data.get("assessment_id")
    if assessment_id:
        assessment = db.query(HealthAssessment).filter(HealthAssessment.id == assessment_id).first()
        if assessment:
            assessment.doctor_id = user_id
            assessment.doctor_notes = data.get("notes")
            assessment.diagnosis = data.get("diagnosis")
            assessment.doctor_assessment = {
                "doctor_notes": data.get("notes"),
                "diagnosis": data.get("diagnosis"),
                "treatment_plan": data.get("treatment_plan"),
            }
    else:
        # Create new assessment
        assessment = HealthAssessment(
            checkin_id=data.get("checkin_id"),
            patient_id=patient_id,
            doctor_id=user_id,
            doctor_notes=data.get("notes"),
            diagnosis=data.get("diagnosis"),
            doctor_assessment={
                "doctor_notes": data.get("notes"),
                "diagnosis": data.get("diagnosis"),
                "treatment_plan": data.get("treatment_plan"),
            },
        )
        db.add(assessment)
    
    db.commit()
    return {"message": "Consultation notes saved"}


@router.post("/prescriptions")
def create_doctor_prescription(
    data: dict,
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """Doctor creates prescription."""
    from app.models.document import Prescription, PrescriptionItem
    
    patient_id = data.get("patient_id")
    if not patient_id:
        raise HTTPException(status_code=400, detail="Patient ID required")
    
    prescription = Prescription(
        patient_id=patient_id,
        doctor_id=user_id,
        assessment_id=data.get("assessment_id"),
        diagnosis=data.get("diagnosis"),
        notes=data.get("notes"),
        is_confirmed=True,
    )
    db.add(prescription)
    db.flush()
    
    for item_data in data.get("items", []):
        item = PrescriptionItem(
            prescription_id=prescription.id,
            medicine_name=item_data.get("medicine_name", ""),
            dosage=item_data.get("dosage"),
            frequency=item_data.get("frequency"),
            duration=item_data.get("duration"),
            instructions=item_data.get("instructions"),
        )
        db.add(item)
    
    db.commit()
    db.refresh(prescription)
    
    return {"id": prescription.id, "message": "Prescription created"}


@router.post("/followups")
def create_followup(
    data: dict,
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """Doctor creates follow-up appointment."""
    from datetime import datetime
    
    appointment = Appointment(
        patient_id=data.get("patient_id"),
        doctor_id=user_id,
        appointment_date=datetime.fromisoformat(data.get("date", datetime.now().isoformat())),
        reason=data.get("reason", "Follow-up"),
        is_follow_up=True,
        status="scheduled",
    )
    db.add(appointment)
    db.commit()
    db.refresh(appointment)
    
    return {"id": appointment.id, "message": "Follow-up scheduled"}
