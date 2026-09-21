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
from app.core.auth import get_current_user_id, get_current_user_role, require_role

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
    if not db.query(PatientProfile).filter(PatientProfile.id == patient_id).first():
        raise HTTPException(status_code=404, detail="Patient not found")

    doctor_assessment = {
        "doctor_notes": data.get("notes"),
        "diagnosis": data.get("diagnosis"),
        "treatment_plan": data.get("treatment_plan"),
    }
    assessment_id = data.get("assessment_id")
    if assessment_id:
        assessment = db.query(HealthAssessment).filter(HealthAssessment.id == assessment_id).first()
        if assessment:
            assessment.doctor_id = user_id
            assessment.doctor_notes = data.get("notes")
            assessment.diagnosis = data.get("diagnosis")
            assessment.doctor_assessment = doctor_assessment
    else:
        # Stand-in assessment for consultations not tied to a specific AI
        # screening. checkin_id is non-nullable, so link to the patient's most
        # recent check-in (or the just-created placeholder if none exists).
        latest_checkin = db.query(HealthCheckin).filter(
            HealthCheckin.patient_id == patient_id
        ).order_by(desc(HealthCheckin.created_at)).first()
        if latest_checkin:
            checkin_id = latest_checkin.id
        else:
            placeholder = HealthCheckin(
                patient_id=patient_id,
                symptoms=[],
                feeling_today="consultation",
                medication_taken=True,
            )
            db.add(placeholder)
            db.flush()
            checkin_id = placeholder.id

        assessment = HealthAssessment(
            checkin_id=checkin_id,
            patient_id=patient_id,
            doctor_id=user_id,
            doctor_notes=data.get("notes"),
            diagnosis=data.get("diagnosis"),
            urgency_level="low",
            recommended_action=(data.get("notes") or "Follow doctor's advice")[:500] or None,
            doctor_assessment=doctor_assessment,
        )
        db.add(assessment)

    db.commit()
    return {"message": "Consultation notes saved"}


@router.post("/prescriptions")
def create_doctor_prescription(
    data: dict,
    user_id: int = Depends(get_current_user_id),
    role: str = Depends(get_current_user_role),
    db: Session = Depends(get_db),
):
    """Doctor creates prescription. Each medicine also becomes a medication
    reminder for the patient so doctor-added medicines show up on the
    patient's Medications page immediately."""
    from app.models.document import Prescription, PrescriptionItem
    from app.models.health import MedicationReminder

    if role != "doctor":
        raise HTTPException(status_code=403, detail="Only doctors can create prescriptions")

    patient_id = data.get("patient_id")
    if not patient_id:
        raise HTTPException(status_code=400, detail="Patient ID required")
    if not db.query(PatientProfile).filter(PatientProfile.id == patient_id).first():
        raise HTTPException(status_code=404, detail="Patient not found")
    
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
    
    created_reminders = 0
    for item_data in data.get("items", []):
        med_name = (item_data.get("medicine_name") or "").strip()
        if not med_name:
            continue
        item = PrescriptionItem(
            prescription_id=prescription.id,
            medicine_name=med_name,
            dosage=item_data.get("dosage"),
            frequency=item_data.get("frequency"),
            duration=item_data.get("duration"),
            instructions=item_data.get("instructions"),
        )
        db.add(item)

        frequency = (item_data.get("frequency") or "").lower()
        time_of_day = "morning"
        if "night" in frequency or "bedtime" in frequency:
            time_of_day = "night"
        elif "afternoon" in frequency or "midday" in frequency:
            time_of_day = "afternoon"
        db.add(MedicationReminder(
            patient_id=patient_id,
            medicine_name=med_name,
            dosage=item_data.get("dosage"),
            frequency=item_data.get("frequency"),
            time_of_day=time_of_day,
            instructions=item_data.get("instructions"),
            source="doctor",
            added_by=user_id,
        ))
        created_reminders += 1
    
    db.commit()
    db.refresh(prescription)
    
    return {
        "id": prescription.id,
        "message": "Prescription created" + (
            f" — {created_reminders} medication reminder(s) added for the patient" if created_reminders else ""
        ),
        "medications_created": created_reminders,
    }


@router.post("/appointments", status_code=201)
def create_doctor_appointment(
    data: dict,
    user_id: int = Depends(get_current_user_id),
    role: str = Depends(get_current_user_role),
    db: Session = Depends(get_db),
):
    if role != "doctor":
        raise HTTPException(status_code=403, detail="Only doctors can schedule appointments")
    """Doctor schedules an appointment for a patient."""
    from datetime import datetime

    patient_id = data.get("patient_id")
    if not patient_id:
        raise HTTPException(status_code=400, detail="Patient ID required")

    profile = db.query(PatientProfile).filter(PatientProfile.id == patient_id).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Patient not found")

    date_str = data.get("date")
    if not date_str:
        raise HTTPException(status_code=400, detail="Appointment date required")
    try:
        appointment_date = datetime.fromisoformat(date_str)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format. Use ISO format (YYYY-MM-DD or YYYY-MM-DDTHH:MM)")

    status = data.get("status", "scheduled")
    if status not in ["scheduled", "completed", "cancelled", "missed"]:
        raise HTTPException(status_code=400, detail="Invalid status")

    appointment = Appointment(
        patient_id=patient_id,
        doctor_id=user_id,
        appointment_date=appointment_date,
        reason=data.get("reason", "Consultation"),
        notes=data.get("notes"),
        status=status,
        is_follow_up=bool(data.get("is_follow_up", False)),
    )
    db.add(appointment)
    db.commit()
    db.refresh(appointment)

    return {"id": appointment.id, "message": "Appointment scheduled", "appointment_id": appointment.id}


@router.get("/appointments")
def list_doctor_appointments(
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """List appointments created by this doctor, with patient names."""
    from app.models.user import User as UserModel

    appointments = db.query(Appointment).filter(
        Appointment.doctor_id == user_id
    ).order_by(desc(Appointment.appointment_date)).all()

    result = []
    for a in appointments:
        patient_profile = db.query(PatientProfile).filter(PatientProfile.id == a.patient_id).first()
        patient_user = (
            db.query(UserModel).filter(UserModel.id == patient_profile.user_id).first()
            if patient_profile else None
        )
        result.append({
            "id": a.id,
            "patient_id": a.patient_id,
            "patient_name": patient_user.full_name if patient_user else "Unknown",
            "appointment_date": str(a.appointment_date) if a.appointment_date else None,
            "reason": a.reason,
            "notes": a.notes,
            "status": a.status,
            "is_follow_up": a.is_follow_up,
            "created_at": str(a.created_at) if a.created_at else None,
        })

    return {"appointments": result, "count": len(result)}


@router.patch("/appointments/{appointment_id}")
def update_appointment(
    appointment_id: int,
    data: dict,
    user_id: int = Depends(get_current_user_id),
    role: str = Depends(get_current_user_role),
    db: Session = Depends(get_db),
):
    """Doctor updates one of their own appointments (reschedule, complete, etc.)."""
    from datetime import datetime

    if role != "doctor":
        raise HTTPException(status_code=403, detail="Only doctors can update appointments")

    appointment = db.query(Appointment).filter(
        Appointment.id == appointment_id,
        Appointment.doctor_id == user_id,
    ).first()
    if not appointment:
        raise HTTPException(status_code=404, detail="Appointment not found")

    if "date" in data:
        try:
            appointment.appointment_date = datetime.fromisoformat(data["date"])
        except (ValueError, TypeError):
            raise HTTPException(status_code=400, detail="Invalid date format. Use ISO format")
    if "reason" in data:
        appointment.reason = data["reason"]
    if "notes" in data:
        appointment.notes = data["notes"]
    if "status" in data:
        if data["status"] not in ["scheduled", "completed", "cancelled", "missed"]:
            raise HTTPException(status_code=400, detail="Invalid status")
        appointment.status = data["status"]
    if "is_follow_up" in data:
        appointment.is_follow_up = bool(data["is_follow_up"])

    db.commit()
    return {"message": "Appointment updated", "id": appointment_id, "status": appointment.status}


@router.delete("/appointments/{appointment_id}")
def cancel_appointment(
    appointment_id: int,
    user_id: int = Depends(get_current_user_id),
    role: str = Depends(get_current_user_role),
    db: Session = Depends(get_db),
):
    if role != "doctor":
        raise HTTPException(status_code=403, detail="Only doctors can cancel appointments")
    """Doctor cancels one of their own scheduled appointments."""
    appointment = db.query(Appointment).filter(
        Appointment.id == appointment_id,
        Appointment.doctor_id == user_id,
    ).first()
    if not appointment:
        raise HTTPException(status_code=404, detail="Appointment not found")

    appointment.status = "cancelled"
    db.commit()
    return {"message": "Appointment cancelled", "id": appointment_id}


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
