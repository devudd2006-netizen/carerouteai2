"""
Care Route Engine - The core differentiating feature.

Answers four questions:
1. WHAT? - What might be happening?
2. HOW SERIOUS? - How urgently should care be sought?
3. WHERE? - What type of healthcare facility is appropriate?
4. WHAT NEXT? - What should happen after consultation?

Recommends appropriate care based on:
- urgency, facility capability, distance, available services, accessibility
"""
import math
import logging
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session

from app.models.facility import HealthcareFacility

logger = logging.getLogger(__name__)

# Care level hierarchy
CARE_LEVELS = {
    "self_care": {
        "name": "Self-Care / Monitor",
        "description": "Symptoms are mild. Monitor at home and follow general health practices.",
        "facility_types": [],
    },
    "phc": {
        "name": "Primary Health Centre (PHC)",
        "description": "Basic healthcare services for routine consultations, minor ailments, and preventive care.",
        "facility_types": ["phc", "clinic"],
    },
    "chc": {
        "name": "Community Health Centre (CHC)",
        "description": "Enhanced healthcare services including specialist consultations and basic diagnostics.",
        "facility_types": ["chc", "clinic"],
    },
    "hospital": {
        "name": "Hospital",
        "description": "Comprehensive medical services including specialist care, diagnostics, and inpatient services.",
        "facility_types": ["hospital"],
    },
    "emergency": {
        "name": "Emergency Department",
        "description": "Immediate emergency medical care for potentially life-threatening conditions.",
        "facility_types": ["hospital", "emergency"],
    },
}


def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate distance between two points in km using Haversine formula."""
    R = 6371  # Earth's radius in km
    
    lat1_r = math.radians(lat1)
    lat2_r = math.radians(lat2)
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    
    a = math.sin(dlat / 2) ** 2 + math.cos(lat1_r) * math.cos(lat2_r) * math.sin(dlon / 2) ** 2
    c = 2 * math.asin(math.sqrt(a))
    
    return R * c


def determine_care_level(urgency_level: str, symptoms: Dict[str, Any]) -> str:
    """Map urgency level to appropriate care level."""
    if urgency_level == "emergency":
        return "emergency"
    elif urgency_level == "high":
        return "hospital"
    elif urgency_level == "moderate":
        # Check if symptoms can be handled at PHC or need CHC
        complex_symptoms = [
            symptoms.get("breathing_difficulty", False),
            symptoms.get("chest_discomfort", False),
            symptoms.get("pain_severity", 0) and symptoms["pain_severity"] >= 7,
        ]
        if any(complex_symptoms):
            return "hospital"
        return "chc"
    else:  # low
        mild_only = not any([
            symptoms.get("breathing_difficulty", False),
            symptoms.get("chest_discomfort", False),
            symptoms.get("fever", False) and (symptoms.get("fever_temperature", 0) or 0) >= 102,
            symptoms.get("pain", False) and (symptoms.get("pain_severity", 0) or 0) >= 5,
            symptoms.get("vomiting", False),
        ])
        if mild_only:
            return "self_care"
        return "phc"


def rank_facilities(
    facilities: List[HealthcareFacility],
    patient_lat: float,
    patient_lon: float,
    care_level: str,
    top_n: int = 5,
) -> List[Dict[str, Any]]:
    """Rank facilities by appropriateness for the care level and distance."""
    care_config = CARE_LEVELS.get(care_level, CARE_LEVELS["phc"])
    suitable_types = set(care_config["facility_types"])
    
    ranked = []
    for facility in facilities:
        distance = haversine_distance(patient_lat, patient_lon, facility.latitude, facility.longitude)
        
        # Score: lower distance = better, appropriate type = better
        type_match = 1.0 if facility.facility_type in suitable_types else 0.5
        distance_score = max(0.1, 1.0 - (distance / 50))  # Normalize, 50km = 0 score
        
        # Emergency facilities get bonus for emergency care level
        emergency_bonus = 1.5 if (care_level == "emergency" and facility.emergency_available) else 1.0
        
        score = type_match * distance_score * emergency_bonus
        
        ranked.append({
            "id": facility.id,
            "name": facility.name,
            "type": facility.facility_type,
            "distance_km": round(distance, 1),
            "services": facility.services or [],
            "emergency_available": facility.emergency_available,
            "contact": facility.contact_number,
            "address": facility.address,
            "latitude": facility.latitude,
            "longitude": facility.longitude,
            "match_score": round(score, 3),
        })
    
    # Sort by score descending
    ranked.sort(key=lambda x: x["match_score"], reverse=True)
    return ranked[:top_n]


async def generate_care_route(
    db: Session,
    urgency_level: str,
    symptoms: Dict[str, Any],
    patient_lat: Optional[float] = None,
    patient_lon: Optional[float] = None,
) -> Dict[str, Any]:
    """Generate complete care route recommendation."""
    care_level = determine_care_level(urgency_level, symptoms)
    care_config = CARE_LEVELS.get(care_level, CARE_LEVELS["phc"])
    
    # WHAT
    what = "Based on the preliminary screening, the following possible health concerns have been identified."
    
    # HOW SERIOUS
    how_serious_map = {
        "self_care": "Symptoms appear mild. Home monitoring may be appropriate.",
        "phc": "Medical evaluation at a primary health centre is recommended.",
        "chc": "A visit to a community health centre or clinic is advisable.",
        "hospital": "Hospital-level evaluation is recommended for your symptoms.",
        "emergency": "URGENT: Immediate emergency medical evaluation is recommended.",
    }
    how_serious = how_serious_map.get(care_level, "Medical evaluation is recommended.")
    
    # WHERE
    where = care_config["description"]
    
    # WHAT NEXT
    what_next_map = {
        "self_care": "Monitor symptoms at home. If symptoms persist more than 2-3 days or worsen, visit a healthcare provider.",
        "phc": "Visit the nearest Primary Health Centre or clinic. Bring any previous medical records.",
        "chc": "Visit a Community Health Centre. They can provide specialist consultations if needed.",
        "hospital": "Visit a hospital. Consider calling ahead to check availability.",
        "emergency": "Seek emergency care immediately. If symptoms are severe, call emergency services.",
    }
    what_next = what_next_map.get(care_level, "Consult a healthcare professional.")
    
    # Find nearby facilities
    recommended_facilities = []
    if patient_lat and patient_lon:
        facilities = db.query(HealthcareFacility).filter(
            HealthcareFacility.is_active == True
        ).all()
        recommended_facilities = rank_facilities(
            facilities, patient_lat, patient_lon, care_level
        )
    
    return {
        "what": what,
        "how_serious": how_serious,
        "where": where,
        "what_next": what_next,
        "recommended_care_level": care_config["name"],
        "care_level_key": care_level,
        "recommended_facilities": recommended_facilities,
        "urgency_explanation": f"Based on your symptoms, the urgency level is assessed as {urgency_level}.",
    }
