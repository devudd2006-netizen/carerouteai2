"""
Authentication and security utilities.
JWT token creation/verification, password hashing, role-based access control.
"""
from datetime import datetime, timedelta, timezone
from typing import Optional
import hashlib
import hmac
import secrets
import json
import base64

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from app.core.config import get_settings

settings = get_settings()
security = HTTPBearer()


def hash_password(password: str) -> str:
    """Hash password using SHA-256 with salt (for demo; use bcrypt in production)."""
    salt = secrets.token_hex(16)
    h = hashlib.sha256(f"{salt}{password}".encode()).hexdigest()
    return f"{salt}${h}"


def verify_password(password: str, hashed: str) -> bool:
    """Verify password against hash."""
    try:
        salt, h = hashed.split("$", 1)
        return hmac.compare_digest(
            hashlib.sha256(f"{salt}{password}".encode()).hexdigest(), h
        )
    except Exception:
        return False


def create_access_token(user_id: int, role: str, expires_delta: Optional[timedelta] = None) -> str:
    """Create JWT access token."""
    now = datetime.now(timezone.utc)
    if expires_delta is None:
        expires_delta = timedelta(hours=settings.JWT_EXPIRATION_HOURS)
    
    # JWT standard: exp/iat must be numeric epoch seconds (datetime is not JSON serializable)
    payload = {
        "sub": str(user_id),
        "role": role,
        "exp": int((now + expires_delta).timestamp()),
        "iat": int(now.timestamp()),
    }
    
    header = base64.urlsafe_b64encode(
        json.dumps({"alg": "HS256", "typ": "JWT"}).encode()
    ).rstrip(b"=").decode()
    
    body = base64.urlsafe_b64encode(json.dumps(payload).encode()).rstrip(b"=").decode()
    
    signature = hmac.new(
        settings.JWT_SECRET.encode(), f"{header}.{body}".encode(), hashlib.sha256
    ).digest()
    sig = base64.urlsafe_b64encode(signature).rstrip(b"=").decode()
    
    return f"{header}.{body}.{sig}"


def decode_access_token(token: str) -> dict:
    """Decode and verify JWT access token."""
    try:
        parts = token.split(".")
        if len(parts) != 3:
            raise HTTPException(status_code=401, detail="Invalid token format")
        
        header, body, sig = parts
        
        expected_sig = base64.urlsafe_b64encode(
            hmac.new(
                settings.JWT_SECRET.encode(), f"{header}.{body}".encode(), hashlib.sha256
            ).digest()
        ).rstrip(b"=").decode()
        
        if not hmac.compare_digest(sig, expected_sig):
            raise HTTPException(status_code=401, detail="Invalid token signature")
        
        padding = 4 - len(body) % 4
        body += "=" * padding
        payload = json.loads(base64.urlsafe_b64decode(body))
        
        exp = datetime.fromtimestamp(payload["exp"], tz=timezone.utc)
        if datetime.now(timezone.utc) > exp:
            raise HTTPException(status_code=401, detail="Token expired")
        
        return payload
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid token")


def get_current_user_id(credentials: HTTPAuthorizationCredentials = Depends(security)) -> int:
    """Extract user ID from JWT token."""
    payload = decode_access_token(credentials.credentials)
    return int(payload["sub"])


def get_current_user_role(credentials: HTTPAuthorizationCredentials = Depends(security)) -> str:
    """Extract user role from JWT token."""
    payload = decode_access_token(credentials.credentials)
    return payload["role"]


def require_role(*roles):
    """Dependency that requires specific roles."""
    def role_checker(
        credentials: HTTPAuthorizationCredentials = Depends(security)
    ) -> dict:
        payload = decode_access_token(credentials.credentials)
        if payload["role"] not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied. Required role: {', '.join(roles)}"
            )
        return {"user_id": int(payload["sub"]), "role": payload["role"]}
    return role_checker
