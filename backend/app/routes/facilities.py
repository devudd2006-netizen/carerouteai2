"""
Healthcare facility routes for the map and care routing.
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from types import SimpleNamespace
from typing import Optional, List

from app.db.database import get_db
from app.models.facility import HealthcareFacility
from app.services.care_route_service import haversine_distance
from app.core.auth import get_current_user_id

router = APIRouter(prefix="/api/facilities", tags=["Facilities"])


def _serialize_facility(f: HealthcareFacility, distance_km: Optional[float] = None) -> dict:
    """Common facility dict so all endpoints return the same shape."""
    return {
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
        "distance_km": round(distance_km, 1) if distance_km is not None else None,
    }


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
        
        result.append(_serialize_facility(f, distance))
    
    # Sort by distance if provided
    if latitude and longitude:
        result.sort(key=lambda x: x.get("distance_km") or 999)
    
    return {"facilities": result, "count": len(result)}


class LiveFacility(BaseModel):
    """A healthcare place sensed live (e.g. from OpenStreetMap Overpass)."""
    id: int
    name: str
    facility_type: str = "hospital"
    latitude: float
    longitude: float
    address: Optional[str] = None
    services: List[str] = Field(default_factory=list)
    emergency_available: bool = False
    opening_hours: Optional[str] = None
    contact_number: Optional[str] = None
    distance_km: Optional[float] = None


class BestRequest(BaseModel):
    latitude: float
    longitude: float
    radius_km: float = 15
    live_facilities: List[LiveFacility] = Field(default_factory=list)


@router.get("/best")
def best_hospitals(
    latitude: Optional[float] = Query(None),
    longitude: Optional[float] = Query(None),
    radius_km: float = Query(15),
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    return _rank_best(db, latitude, longitude, radius_km)


@router.post("/best")
def best_hospitals_live(
    payload: BestRequest,
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """Same ranking as GET /best, with live-sensed facilities merged in.

    The frontend senses real healthcare places around the user (OpenStreetMap
    Overpass) and posts them here; catalogue records keep priority on name
    collisions. Live clinics/pharmacies are ignored — this ranks hospitals.
    """
    return _rank_best(
        db, payload.latitude, payload.longitude, payload.radius_km,
        [lf.model_dump() for lf in payload.live_facilities],
    )


def _rank_best(
    db: Session,
    latitude: Optional[float],
    longitude: Optional[float],
    radius_km: float,
    live_facilities: Optional[List[dict]] = None,
) -> dict:
    """Shared ranking used by GET /best (catalogue only) and POST /best
    (catalogue merged with live-sensed facilities)."""
    hospitals = list(
        db.query(HealthcareFacility).filter(
            HealthcareFacility.is_active == True,  # noqa: E712
            HealthcareFacility.facility_type.in_(["hospital", "emergency"]),
        ).all()
    )

    # Fold live-sensed hospitals into the ranking. The curated catalogue wins
    # on name collisions; live entries get catalogue-compatible attributes.
    for lf in live_facilities or []:
        if (lf.get("facility_type") or "") not in ("hospital", "emergency"):
            continue
        lname = (lf.get("name") or "").strip().lower()
        if not lname or any(h.name.strip().lower() == lname for h in hospitals):
            continue
        hospitals.append(SimpleNamespace(
            id=lf["id"],
            name=lf["name"],
            facility_type=lf.get("facility_type") or "hospital",
            latitude=lf["latitude"],
            longitude=lf["longitude"],
            address=lf.get("address"),
            village=None,
            district=None,
            services=lf.get("services") or [],
            emergency_available=bool(lf.get("emergency_available")),
            opening_hours=lf.get("opening_hours"),
            contact_number=lf.get("contact_number"),
            accessibility_info=None,
        ))

    def capability(h: HealthcareFacility) -> float:
        services = h.services or []
        score = 0.0
        score += min(len(services), 8) * 0.6          # breadth of services (max 4.8)
        score += 2.0 if h.emergency_available else 0.0  # emergency readiness
        score += 1.0 if (h.opening_hours or "") in ("24/7", "24x7", "24 hours") else 0.0
        if "surgery" in services:
            score += 1.0
        if "cardiology" in services:
            score += 0.8
        if "diagnostics" in services:
            score += 0.6
        return score

    scored = []
    for h in hospitals:
        dist = haversine_distance(latitude, longitude, h.latitude, h.longitude) if latitude is not None and longitude is not None else None
        scored.append((h, capability(h), dist))

    def to_dict(h: HealthcareFacility, cap: float, dist: Optional[float]) -> dict:
        d = _serialize_facility(h, dist)
        d["capability_score"] = round(cap, 1)
        if dist is not None:
            # Proximity-led score: each extra km costs more than any capability
            # difference can buy back, so closer hospitals always rank above
            # distant ones. Capability separates hospitals at the same distance
            # scale (banded in 1-km buckets).
            distance_band = int(dist)  # 1-km buckets
            d["rank_score"] = round(-distance_band + cap / 10.0, 2)
        else:
            d["rank_score"] = round(cap, 2)
        return d

    # Nearby best: proximity-first within the radius.
    nearby_best = []
    used_fallback = False
    if latitude is not None and longitude is not None:
        nearby_scored = [s for s in scored if s[2] is not None and s[2] <= radius_km]
        if not nearby_scored:
            # Nothing within the radius: take the closest hospitals anywhere and
            # flag it so the UI can say "nearest hospitals" honestly.
            used_fallback = True
            nearby_scored = sorted(scored, key=lambda s: s[2] if s[2] is not None else 9999)[:3]
        nearby_scored.sort(key=lambda s: to_dict(s[0], s[1], s[2])["rank_score"], reverse=True)
        nearby_best = [to_dict(h, cap, dist) for h, cap, dist in nearby_scored[:6]]

    # Overall best: pure capability, any distance
    overall_best = sorted(scored, key=lambda s: s[1], reverse=True)
    overall_best = [to_dict(h, cap, dist) for h, cap, dist in overall_best[:6]]

    return {
        "nearby_best": nearby_best,
        "overall_best": overall_best,
        "radius_km": radius_km,
        "used_fallback": used_fallback if latitude is not None else False,
        "user_location": {"latitude": latitude, "longitude": longitude} if latitude is not None else None,
    }


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
