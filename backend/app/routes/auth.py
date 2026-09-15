"""
Authentication routes: register, login, profile.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.models.user import User, UserRole
from app.models.patient import PatientProfile
from app.schemas.auth import (
    UserRegister, UserLogin, TokenResponse,
    UserResponse, UserUpdate, PasswordReset,
)
from app.core.auth import hash_password, verify_password, create_access_token, get_current_user_id

router = APIRouter(prefix="/api/auth", tags=["Authentication"])


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
def register(data: UserRegister, db: Session = Depends(get_db)):
    """Register a new user."""
    # Check existing user
    existing = db.query(User).filter(User.email == data.email).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Validate role
    role = data.role if data.role in ["patient", "doctor", "admin", "community_authority"] else "patient"
    
    # Create user
    user = User(
        email=data.email,
        password_hash=hash_password(data.password),
        full_name=data.full_name,
        role=role,
        phone=data.phone,
    )
    db.add(user)
    db.flush()
    
    # Create patient profile if role is patient
    if role == "patient":
        profile = PatientProfile(user_id=user.id)
        db.add(profile)
    
    db.commit()
    db.refresh(user)
    
    token = create_access_token(user.id, user.role)
    return TokenResponse(
        access_token=token,
        user={
            "id": user.id,
            "email": user.email,
            "full_name": user.full_name,
            "role": user.role,
        }
    )


@router.post("/login", response_model=TokenResponse)
def login(data: UserLogin, db: Session = Depends(get_db)):
    """Login with email and password."""
    user = db.query(User).filter(User.email == data.email).first()
    if not user or not verify_password(data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is disabled"
        )
    
    token = create_access_token(user.id, user.role)
    return TokenResponse(
        access_token=token,
        user={
            "id": user.id,
            "email": user.email,
            "full_name": user.full_name,
            "role": user.role,
        }
    )


@router.get("/me", response_model=UserResponse)
def get_me(user_id: int = Depends(get_current_user_id), db: Session = Depends(get_db)):
    """Get current user profile."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    return UserResponse(
        id=user.id,
        email=user.email,
        full_name=user.full_name,
        role=user.role,
        phone=user.phone,
        is_active=user.is_active,
        health_data_sharing=user.health_data_sharing,
        emergency_info_sharing=user.emergency_info_sharing,
        community_analytics_participation=user.community_analytics_participation,
        created_at=str(user.created_at) if user.created_at else None,
    )


@router.put("/me", response_model=UserResponse)
def update_me(data: UserUpdate, user_id: int = Depends(get_current_user_id), db: Session = Depends(get_db)):
    """Update current user profile."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(user, key, value)
    
    db.commit()
    db.refresh(user)
    
    return UserResponse(
        id=user.id,
        email=user.email,
        full_name=user.full_name,
        role=user.role,
        phone=user.phone,
        is_active=user.is_active,
        health_data_sharing=user.health_data_sharing,
        emergency_info_sharing=user.emergency_info_sharing,
        community_analytics_participation=user.community_analytics_participation,
    )
