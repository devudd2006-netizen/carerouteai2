"""
Emergency routes: evaluate, health card, emergency events.
"""
import secrets
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime, timedelta, timezone

from app.db.database import get_db
from app.models.user import User
from app.models.patient import PatientProfile, EmergencyContact
from app.models.facility import HealthcareFacility
from app.models.emergency import EmergencyEvent, EmergencyHealthCard
from app.services.red_flag_engine import evaluate_red_flags
from app.services.care_route_service import haversine_distance
from app.core.auth import get_current_user_id

router = APIRouter(prefix="/api/emergency", tags=["Emergency"])


@router.post("/evaluate")
async def evaluate_emergency(
    data: dict,
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """Evaluate symptoms for potential emergency."""
    symptoms = data.get("symptoms", {})
    
    is_emergency, red_flags, guidance = evaluate_red_flags(symptoms)
    
    profile = db.query(PatientProfile).filter(PatientProfile.user_id == user_id).first()
    
    # Find nearest emergency facility
    nearest_emergency = None
    if profile and profile.latitude and profile.longitude:
        facilities = db.query(HealthcareFacility).filter(
            HealthcareFacility.emergency_available == True,
            HealthcareFacility.is_active == True,
        ).all()
        
        for f in facilities:
            dist = haversine_distance(profile.latitude, profile.longitude, f.latitude, f.longitude)
            if nearest_emergency is None or dist < nearest_emergency["distance_km"]:
                nearest_emergency = {
                    "id": f.id,
                    "name": f.name,
                    "distance_km": round(dist, 1),
                    "contact": f.contact_number,
                    "address": f.address,
                    "latitude": f.latitude,
                    "longitude": f.longitude,
                }
    
    # Create emergency event if detected
    event_id = None
    if is_emergency:
        event = EmergencyEvent(
            patient_id=profile.id if profile else None,
            symptoms=symptoms,
            red_flags=[rf["description"] for rf in red_flags],
            status="detected",
            guidance=guidance,
            recommended_facility_name=nearest_emergency["name"] if nearest_emergency else None,
            location_latitude=profile.latitude if profile else None,
            location_longitude=profile.longitude if profile else None,
            is_demo=True,  # Clearly labeled demo
        )
        db.add(event)
        db.flush()
        event_id = event.id
    
    db.commit()
    
    return {
        "is_emergency": is_emergency,
        "red_flags": red_flags,
        "guidance": guidance,
        "nearest_emergency_facility": nearest_emergency,
        "event_id": event_id,
        "is_demo_workflow": True,
        "demo_notice": "This is a demo emergency workflow. No real emergency services are contacted. In a real implementation, configured emergency services would be notified with explicit user consent.",
    }


@router.post("/health-card")
def generate_health_card(
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """Generate Emergency Health Card with minimum necessary information."""
    profile = db.query(PatientProfile).filter(PatientProfile.user_id == user_id).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Patient profile not found")
    
    user = db.query(User).filter(User.id == user_id).first()
    
    # Calculate age
    age = None
    if profile.date_of_birth:
        from datetime import date
        age = (date.today() - profile.date_of_birth).days // 365
    
    # Get emergency contact
    contact = db.query(EmergencyContact).filter(
        EmergencyContact.patient_id == profile.id,
        EmergencyContact.is_primary == True,
    ).first()
    if not contact:
        contact = db.query(EmergencyContact).filter(
            EmergencyContact.patient_id == profile.id,
        ).first()
    
    # Parse allergies and conditions
    import json
    try:
        allergies = json.loads(profile.allergies) if profile.allergies else []
    except (json.JSONDecodeError, TypeError):
        allergies = [profile.allergies] if profile.allergies else []
    
    try:
        conditions = json.loads(profile.chronic_conditions) if profile.chronic_conditions else []
    except (json.JSONDecodeError, TypeError):
        conditions = [profile.chronic_conditions] if profile.chronic_conditions else []
    
    # Create shareable card
    share_token = secrets.token_urlsafe(32)
    expires_at = datetime.now(timezone.utc) + timedelta(hours=24)
    
    card = EmergencyHealthCard(
        patient_id=profile.id,
        patient_name=user.full_name,
        age=age,
        blood_group=profile.blood_group,
        allergies=allergies,
        medical_conditions=conditions,
        current_medications=[],  # Only from verified prescriptions
        emergency_contact_name=contact.name if contact else None,
        emergency_contact_phone=contact.phone if contact else None,
        current_location=f"{profile.village}, {profile.district}" if profile.village else None,
        share_token=share_token,
        expires_at=expires_at,
    )
    db.add(card)
    db.commit()
    db.refresh(card)
    
    return {
        "card_id": card.id,
        "share_token": share_token,
        "patient_name": card.patient_name,
        "age": card.age,
        "blood_group": card.blood_group,
        "allergies": card.allergies,
        "medical_conditions": card.medical_conditions,
        "emergency_contact_name": card.emergency_contact_name,
        "emergency_contact_phone": card.emergency_contact_phone,
        "current_location": card.current_location,
        "expires_at": str(expires_at),
        "note": "This card contains minimum necessary information for emergency situations.",
    }


@router.get("/health-card/{share_token}")
def get_shared_health_card(share_token: str, db: Session = Depends(get_db)):
    """Access a shared emergency health card (public, time-limited)."""
    card = db.query(EmergencyHealthCard).filter(
        EmergencyHealthCard.share_token == share_token,
        EmergencyHealthCard.is_valid == True,
    ).first()
    
    if not card:
        raise HTTPException(status_code=404, detail="Health card not found or expired")
    
    # Check expiry
    if card.expires_at and card.expires_at < datetime.now(timezone.utc):
        card.is_valid = False
        db.commit()
        raise HTTPException(status_code=410, detail="Health card has expired")
    
    return {
        "patient_name": card.patient_name,
        "age": card.age,
        "blood_group": card.blood_group,
        "allergies": card.allergies,
        "medical_conditions": card.medical_conditions,
        "current_medications": card.current_medications,
        "current_symptoms": card.current_symptoms,
        "emergency_contact_name": card.emergency_contact_name,
        "emergency_contact_phone": card.emergency_contact_phone,
        "current_location": card.current_location,
        "expires_at": str(card.expires_at),
    }
