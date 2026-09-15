"""
Community Health Pulse routes.
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.db.database import get_db
from app.models.community import (
    Community, CommunityHealthSignal, CommunityPriorityScore, MedicalCampRecommendation
)
from app.services.community_service import calculate_all_priority_scores, generate_camp_recommendation
from app.core.auth import get_current_user_id, require_role

router = APIRouter(prefix="/api/community", tags=["Community Health"])


@router.get("/overview")
async def community_overview(
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """Get community health overview dashboard data."""
    communities = db.query(Community).all()
    signals = db.query(CommunityHealthSignal).all()
    scores = db.query(CommunityPriorityScore).all()
    
    # Calculate fresh scores
    score_results = await calculate_all_priority_scores(db)
    
    high_priority = sum(1 for s in scores if s.priority_level in ["high", "critical"])
    
    # Symptom trends
    symptom_counts = {}
    for s in signals:
        cat = s.symptom_category or "unknown"
        symptom_counts[cat] = symptom_counts.get(cat, 0) + (s.report_count or 1)
    
    trend_data = [{"category": k, "count": v} for k, v in sorted(symptom_counts.items(), key=lambda x: -x[1])]
    
    return {
        "communities_monitored": len(communities),
        "high_priority_areas": high_priority,
        "healthcare_gaps": len([s for s in scores if s.priority_score and s.priority_score > 50]),
        "total_signals": len(signals),
        "priority_distribution": {
            "critical": sum(1 for s in scores if s.priority_level == "critical"),
            "high": sum(1 for s in scores if s.priority_level == "high"),
            "medium": sum(1 for s in scores if s.priority_level == "medium"),
            "low": sum(1 for s in scores if s.priority_level == "low"),
        },
        "symptom_trends": trend_data[:10],
    }


@router.get("/priority-map")
async def priority_map(
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """Get priority score map data for all communities."""
    scores = await calculate_all_priority_scores(db)
    return {"communities": scores, "count": len(scores)}


@router.get("/communities")
def list_communities(db: Session = Depends(get_db)):
    """List all communities."""
    communities = db.query(Community).all()
    return {
        "communities": [
            {
                "id": c.id,
                "name": c.name,
                "village": c.village,
                "district": c.district,
                "latitude": c.latitude,
                "longitude": c.longitude,
                "population": c.population,
                "distance_to_nearest_facility_km": c.distance_to_nearest_facility_km,
            }
            for c in communities
        ]
    }


@router.get("/communities/{community_id}")
def get_community_detail(community_id: int, db: Session = Depends(get_db)):
    """Get detailed community information."""
    community = db.query(Community).filter(Community.id == community_id).first()
    if not community:
        raise HTTPException(status_code=404, detail="Community not found")
    
    signals = db.query(CommunityHealthSignal).filter(
        CommunityHealthSignal.community_id == community_id
    ).order_by(desc(CommunityHealthSignal.created_at)).all()
    
    score = db.query(CommunityPriorityScore).filter(
        CommunityPriorityScore.community_id == community_id
    ).first()
    
    return {
        "community": {
            "id": community.id,
            "name": community.name,
            "village": community.village,
            "district": community.district,
            "latitude": community.latitude,
            "longitude": community.longitude,
            "population": community.population,
            "distance_to_nearest_facility_km": community.distance_to_nearest_facility_km,
            "has_phc": community.has_phc,
            "has_chc": community.has_chc,
            "has_hospital": community.has_hospital,
            "elderly_population_pct": community.elderly_population_pct,
            "children_population_pct": community.children_population_pct,
            "pregnant_women_count": community.pregnant_women_count,
            "accessibility_score": community.accessibility_score,
        },
        "priority_score": {
            "score": score.priority_score if score else None,
            "level": score.priority_level if score else None,
            "reasons": score.reasons if score else [],
        } if score else None,
        "signals": [
            {
                "id": s.id,
                "type": s.signal_type,
                "symptom_category": s.symptom_category,
                "report_count": s.report_count,
                "severity": s.severity_indicator,
                "created_at": str(s.created_at) if s.created_at else None,
            }
            for s in signals
        ],
    }


@router.post("/camp-recommendation")
async def camp_recommendation(
    data: dict = {},
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """Generate medical camp recommendations."""
    community_id = data.get("community_id")
    recommendations = await generate_camp_recommendation(db, community_id)
    return {"recommendations": recommendations, "count": len(recommendations)}


@router.get("/camp-recommendations")
def list_camp_recommendations(db: Session = Depends(get_db)):
    """List existing camp recommendations."""
    recs = db.query(MedicalCampRecommendation).order_by(
        desc(MedicalCampRecommendation.created_at)
    ).limit(10).all()
    
    return {
        "recommendations": [
            {
                "id": r.id,
                "community_id": r.community_id,
                "recommended_location": r.recommended_location,
                "priority_score": r.priority_score,
                "reason": r.reason,
                "population_affected": r.population_affected,
                "suggested_services": r.suggested_services,
                "suggested_duration_days": r.suggested_duration_days,
                "is_implemented": r.is_implemented,
                "created_at": str(r.created_at) if r.created_at else None,
            }
            for r in recs
        ]
    }
