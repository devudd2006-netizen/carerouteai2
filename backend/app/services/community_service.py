"""
Community Health Intelligence Service.

Handles:
- Community priority scoring
- Healthcare gap analysis
- Medical camp recommendations
- Aggregated health data analysis
"""
import math
import logging
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.models.community import (
    Community, CommunityHealthSignal, CommunityPriorityScore, MedicalCampRecommendation
)
from app.models.facility import HealthcareFacility

logger = logging.getLogger(__name__)


def calculate_priority_score(community: Community, signals: List[CommunityHealthSignal]) -> Dict[str, Any]:
    """
    Calculate Care Priority Score for a community.
    
    Factors:
    - Distance to nearest facility (0-100)
    - Population vulnerability (0-100)
    - Health demand signals (0-100)
    - Facility availability (0-100)
    - Accessibility (0-100)
    """
    # Distance score: farther = higher priority
    distance = community.distance_to_nearest_facility_km or 20
    distance_score = min(100, (distance / 30) * 100)  # 30km = max score
    
    # Population vulnerability
    vuln_pct = (community.elderly_population_pct or 0) + (community.children_population_pct or 0)
    pregnancy_factor = min(20, (community.pregnant_women_count or 0) * 2)
    vuln_score = min(100, vuln_pct * 2 + pregnancy_factor)
    
    # Health demand: based on recent signals
    total_signals = sum(s.report_count for s in signals) if signals else 0
    high_severity = sum(1 for s in signals if (s.severity_indicator or 0) > 0.6) if signals else 0
    demand_score = min(100, total_signals * 5 + high_severity * 15)
    
    # Facility availability (inverse - fewer facilities = higher priority)
    facility_flags = sum([
        community.has_phc,
        community.has_chc,
        community.has_hospital,
        community.has_pharmacy,
    ])
    facility_score = max(0, 100 - (facility_flags * 25))
    
    # Accessibility
    accessibility_score = max(0, 100 - ((community.accessibility_score or 0.5) * 100))
    
    # Weighted average
    priority = (
        distance_score * 0.25 +
        vuln_score * 0.20 +
        demand_score * 0.25 +
        facility_score * 0.15 +
        accessibility_score * 0.15
    )
    
    # Determine level
    if priority >= 75:
        level = "critical"
    elif priority >= 50:
        level = "high"
    elif priority >= 25:
        level = "medium"
    else:
        level = "low"
    
    # Generate reasons
    reasons = []
    if distance > 10:
        reasons.append(f"{distance:.0f} km from nearest suitable facility")
    if facility_flags < 2:
        reasons.append("Limited healthcare facility availability")
    if vuln_pct > 30:
        reasons.append("High vulnerable population percentage")
    if total_signals > 5:
        reasons.append("Increased health-service demand signals")
    if (community.accessibility_score or 1) < 0.4:
        reasons.append("Poor accessibility")
    if pregnancy_factor > 10:
        reasons.append(f"{community.pregnant_women_count} pregnant women in community")
    
    return {
        "priority_score": round(priority, 1),
        "priority_level": level,
        "distance_score": round(distance_score, 1),
        "population_vulnerability_score": round(vuln_score, 1),
        "health_demand_score": round(demand_score, 1),
        "facility_availability_score": round(facility_score, 1),
        "accessibility_score_calc": round(accessibility_score, 1),
        "reasons": reasons,
    }


async def calculate_all_priority_scores(db: Session) -> List[Dict[str, Any]]:
    """Calculate priority scores for all communities."""
    communities = db.query(Community).all()
    results = []
    
    for community in communities:
        signals = db.query(CommunityHealthSignal).filter(
            CommunityHealthSignal.community_id == community.id
        ).all()
        
        score_data = calculate_priority_score(community, signals)
        
        # Save or update score
        existing = db.query(CommunityPriorityScore).filter(
            CommunityPriorityScore.community_id == community.id
        ).first()
        
        if existing:
            existing.priority_score = score_data["priority_score"]
            existing.priority_level = score_data["priority_level"]
            existing.distance_score = score_data["distance_score"]
            existing.population_vulnerability_score = score_data["population_vulnerability_score"]
            existing.health_demand_score = score_data["health_demand_score"]
            existing.facility_availability_score = score_data["facility_availability_score"]
            existing.accessibility_score = score_data["accessibility_score_calc"]
            existing.reasons = score_data["reasons"]
        else:
            db_score = CommunityPriorityScore(
                community_id=community.id,
                priority_score=score_data["priority_score"],
                priority_level=score_data["priority_level"],
                distance_score=score_data["distance_score"],
                population_vulnerability_score=score_data["population_vulnerability_score"],
                health_demand_score=score_data["health_demand_score"],
                facility_availability_score=score_data["facility_availability_score"],
                accessibility_score=score_data["accessibility_score_calc"],
                reasons=score_data["reasons"],
            )
            db.add(db_score)
        
        results.append({
            "community_id": community.id,
            "community_name": community.name,
            "village": community.village,
            "district": community.district,
            "latitude": community.latitude,
            "longitude": community.longitude,
            "population": community.population,
            **score_data,
        })
    
    db.commit()
    return results


async def generate_camp_recommendation(
    db: Session,
    community_id: Optional[int] = None,
) -> List[Dict[str, Any]]:
    """Generate medical camp recommendations for high-priority communities."""
    query = db.query(CommunityPriorityScore).order_by(
        CommunityPriorityScore.priority_score.desc()
    )
    
    if community_id:
        query = query.filter(CommunityPriorityScore.community_id == community_id)
    
    high_priority = query.filter(
        CommunityPriorityScore.priority_level.in_(["high", "critical"])
    ).limit(5).all()
    
    recommendations = []
    
    for score in high_priority:
        community = db.query(Community).filter(Community.id == score.community_id).first()
        if not community:
            continue
        
        # Determine suggested services based on community profile
        services = ["General consultation", "Basic diagnostics"]
        if community.pregnant_women_count and community.pregnant_women_count > 0:
            services.append("Maternal health screening")
        if community.elderly_population_pct and community.elderly_population_pct > 20:
            services.append("Chronic disease screening (diabetes, hypertension)")
        services.append("Blood pressure screening")
        services.append("Blood sugar screening")
        
        # Calculate duration based on population
        population = community.population or 500
        if population > 2000:
            duration = 5
        elif population > 1000:
            duration = 3
        else:
            duration = 2
        
        # Generate recommendation
        recommendation = MedicalCampRecommendation(
            community_id=community.id,
            recommended_location=f"{community.village or community.name}, {community.district or ''}",
            latitude=community.latitude,
            longitude=community.longitude,
            priority_score=score.priority_score,
            reason=f"High healthcare access gap ({community.distance_to_nearest_facility_km or 'unknown'} km to nearest facility) + high vulnerable population + increased health demand.",
            population_affected=population,
            healthcare_gaps={
                "distance_to_facility_km": community.distance_to_nearest_facility_km,
                "has_phc": community.has_phc,
                "has_hospital": community.has_hospital,
                "accessibility": community.accessibility_score,
            },
            suggested_services=services,
            suggested_duration_days=duration,
        )
        db.add(recommendation)
        db.flush()
        
        recommendations.append({
            "id": recommendation.id,
            "community_name": community.name,
            "recommended_location": recommendation.recommended_location,
            "latitude": recommendation.latitude,
            "longitude": recommendation.longitude,
            "priority_score": recommendation.priority_score,
            "priority_level": score.priority_level,
            "reason": recommendation.reason,
            "population_affected": recommendation.population_affected,
            "healthcare_gaps": recommendation.healthcare_gaps,
            "suggested_services": recommendation.suggested_services,
            "suggested_duration_days": recommendation.suggested_duration_days,
        })
    
    db.commit()
    return recommendations
