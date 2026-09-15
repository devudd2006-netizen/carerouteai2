"""
Patient profile schemas.
"""
from pydantic import BaseModel
from typing import Optional, List
from datetime import date


class PatientProfileCreate(BaseModel):
    date_of_birth: Optional[date] = None
    gender: Optional[str] = None
    blood_group: Optional[str] = None
    address: Optional[str] = None
    village: Optional[str] = None
    district: Optional[str] = None
    state: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    preferred_language: str = "en"
    allergies: Optional[str] = None
    chronic_conditions: Optional[str] = None


class PatientProfileUpdate(BaseModel):
    date_of_birth: Optional[date] = None
    gender: Optional[str] = None
    blood_group: Optional[str] = None
    address: Optional[str] = None
    village: Optional[str] = None
    district: Optional[str] = None
    state: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    preferred_language: Optional[str] = None
    allergies: Optional[str] = None
    chronic_conditions: Optional[str] = None


class PatientProfileResponse(BaseModel):
    id: int
    user_id: int
    date_of_birth: Optional[date] = None
    gender: Optional[str] = None
    blood_group: Optional[str] = None
    address: Optional[str] = None
    village: Optional[str] = None
    district: Optional[str] = None
    state: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    preferred_language: Optional[str] = None
    allergies: Optional[str] = None
    chronic_conditions: Optional[str] = None
    user_name: Optional[str] = None
    user_email: Optional[str] = None
    user_phone: Optional[str] = None

    model_config = {"from_attributes": True}


class EmergencyContactCreate(BaseModel):
    name: str
    relationship_type: Optional[str] = None
    phone: str
    is_primary: bool = False


class EmergencyContactResponse(BaseModel):
    id: int
    name: str
    relationship_type: Optional[str] = None
    phone: str
    is_primary: bool

    model_config = {"from_attributes": True}


class DoctorProfileResponse(BaseModel):
    id: int
    user_id: int
    specialization: Optional[str] = None
    license_number: Optional[str] = None
    hospital_name: Optional[str] = None
    experience_years: Optional[int] = None
    bio: Optional[str] = None
    user_name: Optional[str] = None
    user_email: Optional[str] = None

    model_config = {"from_attributes": True}
