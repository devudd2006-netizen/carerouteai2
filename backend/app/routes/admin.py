"""
Admin dashboard routes.
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import desc, func

from app.db.database import get_db
from app.models.user import User, UserRole
from app.models.patient import PatientProfile
from app.models.health import HealthCheckin, HealthAssessment, CarePlan, Appointment
from app.models.facility import HealthcareFacility
from app.models.community import Community, CommunityPriorityScore
from app.core.auth import get_current_user_id, require_role

router = APIRouter(prefix="/api/admin", tags=["Admin"])


@router.get("/dashboard")
def admin_dashboard(
    user_data: dict = Depends(require_role("admin", "community_authority")),
    db: Session = Depends(get_db),
):
    """Get admin dashboard statistics."""
    total_patients = db.query(func.count(PatientProfile.id)).scalar() or 0
    active_doctors = db.query(func.count(User.id)).filter(User.role == "doctor", User.is_active == True).scalar() or 0
    total_facilities = db.query(func.count(HealthcareFacility.id)).filter(HealthcareFacility.is_active == True).scalar() or 0
    
    # High-risk alerts (emergency or high urgency in last 7 days)
    from datetime import datetime, timedelta
    week_ago = datetime.now() - timedelta(days=7)
    high_risk = db.query(func.count(HealthAssessment.id)).filter(
        HealthAssessment.urgency_level.in_(["high", "emergency"]),
        HealthAssessment.created_at >= week_ago,
    ).scalar() or 0
    
    # Pending follow-ups
    pending_followups = db.query(func.count(Appointment.id)).filter(
        Appointment.status == "scheduled",
        Appointment.is_follow_up == True,
    ).scalar() or 0
    
    # High-priority communities
    high_priority_communities = db.query(func.count(CommunityPriorityScore.id)).filter(
        CommunityPriorityScore.priority_level.in_(["high", "critical"])
    ).scalar() or 0
    
    # Total users
    total_users = db.query(func.count(User.id)).scalar() or 0
    
    # Recent signups
    recent_signups = db.query(func.count(User.id)).filter(
        User.created_at >= week_ago
    ).scalar() or 0
    
    return {
        "total_patients": total_patients,
        "active_doctors": active_doctors,
        "healthcare_facilities": total_facilities,
        "high_risk_alerts": high_risk,
        "pending_followups": pending_followups,
        "high_priority_communities": high_priority_communities,
        "total_users": total_users,
        "recent_signups": recent_signups,
    }


@router.get("/users")
def list_users(
    user_data: dict = Depends(require_role("admin")),
    db: Session = Depends(get_db),
):
    """List all users."""
    users = db.query(User).order_by(desc(User.created_at)).all()
    return {
        "users": [
            {
                "id": u.id,
                "email": u.email,
                "full_name": u.full_name,
                "role": u.role,
                "is_active": u.is_active,
                "created_at": str(u.created_at) if u.created_at else None,
            }
            for u in users
        ]
    }


@router.get("/stats")
def admin_stats(
    user_data: dict = Depends(require_role("admin")),
    db: Session = Depends(get_db),
):
    """Get detailed admin statistics."""
    # Check-in trend (last 30 days)
    from datetime import datetime, timedelta
    
    checkin_trend = []
    for i in range(30):
        day = datetime.now() - timedelta(days=i)
        count = db.query(func.count(HealthCheckin.id)).filter(
            func.date(HealthCheckin.created_at) == day.date()
        ).scalar() or 0
        checkin_trend.append({"date": day.strftime("%Y-%m-%d"), "count": count})
    
    checkin_trend.reverse()
    
    # Urgency distribution
    urgency_dist = db.query(
        HealthAssessment.urgency_level, func.count(HealthAssessment.id)
    ).group_by(HealthAssessment.urgency_level).all()
    
    return {
        "checkin_trend": checkin_trend,
        "urgency_distribution": {level: count for level, count in urgency_dist if level},
    }
