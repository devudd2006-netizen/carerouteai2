"""
Core configuration for CareRoute AI backend.
Loads environment variables and provides settings.
"""
import os
from functools import lru_cache
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Application
    APP_NAME: str = "CareRoute AI"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True
    
    # Database
    DATABASE_URL: str = "postgresql://postgres:postgres@localhost:5432/careroute"
    
    # Authentication
    JWT_SECRET: str = "change-this-to-a-strong-secret-key-in-production"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRATION_HOURS: int = 72
    
    # CORS
    FRONTEND_URL: str = "http://localhost:5173"
    APP_URL: str = "http://localhost:8000"
    
    # AI - Google Gemini
    GEMINI_API_KEY: str = ""
    
    # File uploads
    UPLOAD_DIR: str = "uploads"
    MAX_FILE_SIZE_MB: int = 20
    ALLOWED_EXTENSIONS: str = "pdf,jpg,jpeg,png,doc,docx"
    
    # Rate limiting
    RATE_LIMIT_PER_MINUTE: int = 60

    model_config = {"env_file": ".env", "extra": "ignore"}


@lru_cache()
def get_settings() -> Settings:
    return Settings()
