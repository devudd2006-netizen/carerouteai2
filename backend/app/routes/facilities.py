"""
Healthcare facility routes for the map and care routing.
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional

from app.db.database import get_db
from app.models.facility import HealthcareFacility
from app.services.care_route_service import haversine_distance
from app.core.auth import get_current_user_id

router = APIRouter(prefix="/api/facilities", tags=["Facilities"])


@router.get("/")
def list_facilities(
    facility_type: Optional[str] = Query(None),
    district: Optional[str] = Query(None),
    latitude: Optional[float] = Query(None),
    longitude: Optional[float] = Query(None),
    radius_km: float = Query(50),
    db: Session = Depends(get_db),
):
    """List healthcare facilities with optional filtering."""
    query = db.query(HealthcareFacility).filter(HealthcareFacility.is_active == True)
    
    if facility_type:
        query = query.filter(HealthcareFacility.facility_type == facility_type)
    if district:
        query = query.filter(HealthcareFacility.district == district)
    
    facilities = query.all()
    
    result = []
    for f in facilities:
        distance = None
        if latitude and longitude:
            distance = haversine_distance(latitude, longitude, f.latitude, f.longitude)
            if distance > radius_km:
                continue
        
        result.append({
            "id": f.id,
            "name": f.name,
            "facility_type": f.facility_type,
            "latitude": f.latitude,
            "longitude": f.longitude,
            "address": f.address,
            "village": f.village,
            "district": f.district,
            "services": f.services or [],
            "emergency_available": f.emergency_available,
            "opening_hours": f.opening_hours,
            "contact_number": f.contact_number,
            "accessibility_info": f.accessibility_info,
            "distance_km": round(distance, 1) if distance else None,
        })
    
    # Sort by distance if provided
    if latitude and longitude:
        result.sort(key=lambda x: x.get("distance_km") or 999)
    
    return {"facilities": result, "count": len(result)}


@router.get("/nearby")
def find_nearby_facilities(
    latitude: float = Query(...),
    longitude: float = Query(...),
    radius_km: float = Query(25),
    facility_type: Optional[str] = Query(None),
    emergency_only: bool = Query(False),
    db: Session = Depends(get_db),
):
    """Find nearby healthcare facilities."""
    query = db.query(HealthcareFacility).filter(HealthcareFacility.is_active == True)
    
    if facility_type:
        query = query.filter(HealthcareFacility.facility_type == facility_type)
    if emergency_only:
        query = query.filter(HealthcareFacility.emergency_available == True)
    
    facilities = query.all()
    
    nearby = []
    for f in facilities:
        distance = haversine_distance(latitude, longitude, f.latitude, f.longitude)
        if distance <= radius_km:
            nearby.append({
                "id": f.id,
                "name": f.name,
                "facility_type": f.facility_type,
                "latitude": f.latitude,
                "longitude": f.longitude,
                "distance_km": round(distance, 1),
                "emergency_available": f.emergency_available,
                "services": f.services or [],
                "contact_number": f.contact_number,
                "address": f.address,
            })
    
    nearby.sort(key=lambda x: x["distance_km"])
    
    return {"facilities": nearby, "count": len(nearby)}


@router.get("/{facility_id}")
def get_facility(facility_id: int, db: Session = Depends(get_db)):
    """Get detailed facility information."""
    facility = db.query(HealthcareFacility).filter(HealthcareFacility.id == facility_id).first()
    if not facility:
        raise HTTPException(status_code=404, detail="Facility not found")
    
    return {
        "id": facility.id,
        "name": facility.name,
        "facility_type": facility.facility_type,
        "latitude": facility.latitude,
        "longitude": facility.longitude,
        "address": facility.address,
        "village": facility.village,
        "district": facility.district,
        "state": facility.state,
        "services": facility.services or [],
        "emergency_available": facility.emergency_available,
        "opening_hours": facility.opening_hours,
        "contact_number": facility.contact_number,
        "accessibility_info": facility.accessibility_info,
    }
