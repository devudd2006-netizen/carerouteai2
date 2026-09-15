"""
Prescription and care plan routes.
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import desc
from typing import Optional, List

from app.db.database import get_db
from app.models.user import User
from app.models.patient import PatientProfile, DoctorProfile
from app.models.health import CarePlan, MedicationReminder, MedicationLog
from app.models.document import Prescription, PrescriptionItem
from app.schemas.health import CarePlanCreate, CarePlanResponse
from app.services.ai_service import ai_prescription_extract
from app.core.auth import get_current_user_id, require_role

router = APIRouter(prefix="/api", tags=["Prescriptions & Care Plans"])


@router.get("/prescriptions")
def list_prescriptions(
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """List prescriptions for current user."""
    profile = db.query(PatientProfile).filter(PatientProfile.user_id == user_id).first()
    if not profile:
        return {"prescriptions": []}
    
    prescriptions = db.query(Prescription).filter(
        Prescription.patient_id == profile.id
    ).order_by(desc(Prescription.created_at)).all()
    
    result = []
    for p in prescriptions:
        items = db.query(PrescriptionItem).filter(
            PrescriptionItem.prescription_id == p.id
        ).all()
        result.append({
            "id": p.id,
            "diagnosis": p.diagnosis,
            "notes": p.notes,
            "is_confirmed": p.is_confirmed,
            "items": [{"id": i.id, "medicine_name": i.medicine_name, "dosage": i.dosage, "frequency": i.frequency, "duration": i.duration, "instructions": i.instructions, "needs_verification": i.needs_verification} for i in items],
            "created_at": str(p.created_at) if p.created_at else None,
        })
    
    return {"prescriptions": result}


@router.post("/prescriptions", status_code=201)
def create_prescription(
    data: dict,
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """
    Patient uploads a prescription (text from a document/photo or typed).
    The text is stored on the prescription so the AI extraction step can read it.
    Extraction results are NOT trusted until the patient confirms them.
    """
    profile = db.query(PatientProfile).filter(PatientProfile.user_id == user_id).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Patient profile not found")
    
    prescription = Prescription(
        patient_id=profile.id,
        # The prescriber, if known. 0/None means "uploaded by patient, doctor unknown".
        doctor_id=data.get("doctor_id") or user_id,
        diagnosis=data.get("diagnosis"),
        notes=data.get("prescription_text") or data.get("notes"),
        document_id=data.get("document_id"),
        is_confirmed=False,
    )
    db.add(prescription)
    db.commit()
    db.refresh(prescription)
    
    return {
        "id": prescription.id,
        "message": "Prescription uploaded. Run extraction, verify the fields, then confirm.",
    }


@router.post("/prescriptions/{prescription_id}/extract")
async def extract_prescription(
    prescription_id: int,
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """AI-extract prescription info from document text."""
    prescription = db.query(Prescription).filter(Prescription.id == prescription_id).first()
    if not prescription:
        raise HTTPException(status_code=404, detail="Prescription not found")
    
    # Get associated document if available
    result = await ai_prescription_extract(
        document_text=prescription.notes or prescription.diagnosis or ""
    )
    
    # Persist extracted medicines as unverified items so the patient can review
    # and confirm each field. AI output is never treated as final.
    saved_items = []
    for med in result.get("medicines", []):
        if not med.get("name"):
            continue  # never invent a medicine name
        item = PrescriptionItem(
            prescription_id=prescription.id,
            medicine_name=med.get("name"),
            dosage=med.get("dosage"),
            frequency=med.get("frequency"),
            duration=med.get("duration"),
            instructions=med.get("instructions"),
            needs_verification=True,
        )
        db.add(item)
        db.flush()
        saved_items.append({
            "id": item.id,
            "medicine_name": item.medicine_name,
            "dosage": item.dosage,
            "frequency": item.frequency,
            "duration": item.duration,
            "instructions": item.instructions,
            "needs_verification": True,
        })
    db.commit()
    
    result["items"] = saved_items
    result["message"] = "Extraction complete. Please verify every field with your doctor/pharmacist before confirming."
    return result


@router.post("/prescriptions/{prescription_id}/confirm")
def confirm_prescription(
    prescription_id: int,
    data: dict,
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """Patient confirms prescription information."""
    prescription = db.query(Prescription).filter(Prescription.id == prescription_id).first()
    if not prescription:
        raise HTTPException(status_code=404, detail="Prescription not found")
    
    prescription.is_confirmed = True
    
    # Update existing extracted items, or add manually-entered ones.
    confirmed_items = data.get("items", data.get("confirmed_items", []))
    for item_data in confirmed_items:
        item = None
        if item_data.get("id"):
            item = db.query(PrescriptionItem).filter(
                PrescriptionItem.id == item_data["id"],
                PrescriptionItem.prescription_id == prescription_id,
            ).first()
        if item:
            item.medicine_name = item_data.get("medicine_name", item.medicine_name)
            item.dosage = item_data.get("dosage", item.dosage)
            item.frequency = item_data.get("frequency", item.frequency)
            item.duration = item_data.get("duration", item.duration)
            item.instructions = item_data.get("instructions", item.instructions)
            item.needs_verification = item_data.get("needs_verification", False)
        elif item_data.get("medicine_name"):
            item = PrescriptionItem(
                prescription_id=prescription_id,
                medicine_name=item_data.get("medicine_name"),
                dosage=item_data.get("dosage"),
                frequency=item_data.get("frequency"),
                duration=item_data.get("duration"),
                instructions=item_data.get("instructions"),
                needs_verification=item_data.get("needs_verification", False),
            )
            db.add(item)
            db.flush()
        
        # Confirmed medication schedules may generate reminders (user-entered
        # schedules are an allowed reminder source; this never modifies a
        # doctor's prescription automatically).
        if item and data.get("create_reminders", True):
            frequency = (item.frequency or "").lower()
            time_of_day = "morning"
            if "night" in frequency or "bedtime" in frequency:
                time_of_day = "night"
            elif "afternoon" in frequency or "midday" in frequency:
                time_of_day = "afternoon"
            db.add(MedicationReminder(
                patient_id=prescription.patient_id,
                medicine_name=item.medicine_name,
                dosage=item.dosage,
                frequency=item.frequency,
                time_of_day=time_of_day,
            ))
    
    db.commit()
    return {"message": "Prescription confirmed. Medication reminders created.", "prescription_id": prescription_id}


# --- Care Plans ---

@router.get("/care-plans")
def list_care_plans(
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """List care plans for current user."""
    profile = db.query(PatientProfile).filter(PatientProfile.user_id == user_id).first()
    if not profile:
        return {"care_plans": []}
    
    plans = db.query(CarePlan).filter(
        CarePlan.patient_id == profile.id
    ).order_by(desc(CarePlan.created_at)).all()
    
    return {"care_plans": plans}


@router.post("/care-plans", status_code=201)
def create_care_plan(
    data: CarePlanCreate,
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """Doctor creates a care plan."""
    patient_id = data.patient_id if hasattr(data, 'patient_id') else None
    patient_data = None
    
    # Check if user is doctor
    doctor = db.query(DoctorProfile).filter(DoctorProfile.user_id == user_id).first()
    if not doctor:
        # Try to find patient profile (for self-created care plans)
        profile = db.query(PatientProfile).filter(PatientProfile.user_id == user_id).first()
        if not profile:
            raise HTTPException(status_code=403, detail="Only doctors can create care plans")
        patient_id = profile.id
    else:
        # Get patient from request body
        pass
    
    if not patient_id:
        raise HTTPException(status_code=400, detail="Patient ID required")
    
    plan = CarePlan(
        patient_id=patient_id,
        doctor_id=user_id,
        title=data.title,
        description=data.description,
        medications=data.medications,
        follow_up_date=data.follow_up_date,
        lab_tests=data.lab_tests,
        doctor_instructions=data.doctor_instructions,
        lifestyle_instructions=data.lifestyle_instructions,
        monitoring_schedule=data.monitoring_schedule,
    )
    db.add(plan)
    db.commit()
    db.refresh(plan)
    
    return {"id": plan.id, "message": "Care plan created successfully"}


# --- Medications ---

@router.get("/medications")
def list_medications(
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """List active medication reminders."""
    profile = db.query(PatientProfile).filter(PatientProfile.user_id == user_id).first()
    if not profile:
        return {"medications": []}
    
    reminders = db.query(MedicationReminder).filter(
        MedicationReminder.patient_id == profile.id,
        MedicationReminder.is_active == True,
    ).all()
    
    # Get recent logs
    logs = db.query(MedicationLog).filter(
        MedicationLog.patient_id == profile.id,
    ).order_by(desc(MedicationLog.logged_at)).limit(100).all()
    
    # Calculate adherence
    taken = sum(1 for l in logs if l.status == "taken")
    total = len(logs)
    adherence = (taken / total * 100) if total > 0 else 100
    
    return {
        "medications": [
            {
                "id": m.id,
                "medicine_name": m.medicine_name,
                "dosage": m.dosage,
                "frequency": m.frequency,
                "time_of_day": m.time_of_day,
            }
            for m in reminders
        ],
        "adherence_percentage": round(adherence, 1),
        "total_doses": total,
        "doses_taken": taken,
    }


@router.post("/medications/{reminder_id}/taken")
def log_medication(
    reminder_id: int,
    data: dict,
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """Log medication as taken/skipped/missed."""
    profile = db.query(PatientProfile).filter(PatientProfile.user_id == user_id).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Patient profile not found")
    
    reminder = db.query(MedicationReminder).filter(
        MedicationReminder.id == reminder_id,
        MedicationReminder.patient_id == profile.id,
    ).first()
    if not reminder:
        raise HTTPException(status_code=404, detail="Medication reminder not found")
    
    status_val = data.get("status", "taken")
    if status_val not in ["taken", "skipped", "missed"]:
        raise HTTPException(status_code=400, detail="Status must be taken, skipped, or missed")
    
    log = MedicationLog(
        reminder_id=reminder_id,
        patient_id=profile.id,
        status=status_val,
    )
    db.add(log)
    db.commit()
    
    return {"message": f"Medication logged as {status_val}"}


# --- Appointments ---

@router.get("/appointments")
def list_appointments(
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """List appointments."""
    from app.models.health import Appointment
    
    profile = db.query(PatientProfile).filter(PatientProfile.user_id == user_id).first()
    if not profile:
        return {"appointments": []}
    
    appointments = db.query(Appointment).filter(
        Appointment.patient_id == profile.id
    ).order_by(Appointment.appointment_date.desc()).all()
    
    return {"appointments": appointments}


@router.post("/appointments", status_code=201)
def create_appointment(
    data: dict,
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """Create an appointment."""
    from app.models.health import Appointment
    from datetime import datetime
    
    profile = db.query(PatientProfile).filter(PatientProfile.user_id == user_id).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Patient profile not found")
    
    appointment = Appointment(
        patient_id=profile.id,
        doctor_id=data.get("doctor_id"),
        facility_id=data.get("facility_id"),
        appointment_date=datetime.fromisoformat(data.get("appointment_date", datetime.now().isoformat())),
        reason=data.get("reason"),
        notes=data.get("notes"),
        is_follow_up=data.get("is_follow_up", False),
    )
    db.add(appointment)
    db.commit()
    db.refresh(appointment)
    
    return {"id": appointment.id, "message": "Appointment scheduled"}
