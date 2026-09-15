"""
Patient profile routes.
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.models.user import User
from app.models.patient import PatientProfile, EmergencyContact
from app.schemas.patient import (
    PatientProfileCreate, PatientProfileUpdate, PatientProfileResponse,
    EmergencyContactCreate, EmergencyContactResponse,
)
from app.core.auth import get_current_user_id, require_role

router = APIRouter(prefix="/api/patient", tags=["Patient"])


@router.get("/profile", response_model=PatientProfileResponse)
def get_profile(user_id: int = Depends(get_current_user_id), db: Session = Depends(get_db)):
    """Get current patient profile."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    profile = db.query(PatientProfile).filter(PatientProfile.user_id == user_id).first()
    if not profile:
        # Create profile if missing
        profile = PatientProfile(user_id=user_id)
        db.add(profile)
        db.commit()
        db.refresh(profile)
    
    return PatientProfileResponse(
        id=profile.id,
        user_id=profile.user_id,
        date_of_birth=profile.date_of_birth,
        gender=profile.gender,
        blood_group=profile.blood_group,
        address=profile.address,
        village=profile.village,
        district=profile.district,
        state=profile.state,
        latitude=profile.latitude,
        longitude=profile.longitude,
        preferred_language=profile.preferred_language,
        allergies=profile.allergies,
        chronic_conditions=profile.chronic_conditions,
        user_name=user.full_name,
        user_email=user.email,
        user_phone=user.phone,
    )


@router.put("/profile", response_model=PatientProfileResponse)
def update_profile(data: PatientProfileUpdate, user_id: int = Depends(get_current_user_id), db: Session = Depends(get_db)):
    """Update patient profile."""
    profile = db.query(PatientProfile).filter(PatientProfile.user_id == user_id).first()
    if not profile:
        profile = PatientProfile(user_id=user_id)
        db.add(profile)
    
    user = db.query(User).filter(User.id == user_id).first()
    
    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(profile, key, value)
    
    db.commit()
    db.refresh(profile)
    
    return PatientProfileResponse(
        id=profile.id,
        user_id=profile.user_id,
        date_of_birth=profile.date_of_birth,
        gender=profile.gender,
        blood_group=profile.blood_group,
        address=profile.address,
        village=profile.village,
        district=profile.district,
        state=profile.state,
        latitude=profile.latitude,
        longitude=profile.longitude,
        preferred_language=profile.preferred_language,
        allergies=profile.allergies,
        chronic_conditions=profile.chronic_conditions,
        user_name=user.full_name if user else None,
        user_email=user.email if user else None,
        user_phone=user.phone if user else None,
    )


@router.get("/emergency-contacts", response_model=list[EmergencyContactResponse])
def get_emergency_contacts(user_id: int = Depends(get_current_user_id), db: Session = Depends(get_db)):
    """Get emergency contacts."""
    profile = db.query(PatientProfile).filter(PatientProfile.user_id == user_id).first()
    if not profile:
        return []
    
    contacts = db.query(EmergencyContact).filter(
        EmergencyContact.patient_id == profile.id
    ).all()
    
    return contacts


@router.post("/emergency-contacts", response_model=EmergencyContactResponse, status_code=201)
def add_emergency_contact(
    data: EmergencyContactCreate,
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """Add an emergency contact."""
    profile = db.query(PatientProfile).filter(PatientProfile.user_id == user_id).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Patient profile not found")
    
    contact = EmergencyContact(
        patient_id=profile.id,
        name=data.name,
        relationship_type=data.relationship_type,
        phone=data.phone,
        is_primary=data.is_primary,
    )
    db.add(contact)
    db.commit()
    db.refresh(contact)
    
    return contact


@router.delete("/emergency-contacts/{contact_id}")
def delete_emergency_contact(
    contact_id: int,
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """Delete an emergency contact."""
    profile = db.query(PatientProfile).filter(PatientProfile.user_id == user_id).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Patient profile not found")
    
    contact = db.query(EmergencyContact).filter(
        EmergencyContact.id == contact_id,
        EmergencyContact.patient_id == profile.id,
    ).first()
    if not contact:
        raise HTTPException(status_code=404, detail="Contact not found")
    
    db.delete(contact)
    db.commit()
    return {"message": "Contact deleted"}
