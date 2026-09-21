"""
CareRoute AI - FastAPI Main Application

"Your Digital Home Health Companion"

A continuous home-to-healthcare coordination platform connecting
patients, doctors, emergency support, and community healthcare intelligence.
"""
import logging
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.core.config import get_settings
from app.db.database import init_db, run_light_migrations

settings = get_settings()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("careroute")

# Create FastAPI app
app = FastAPI(
    title="CareRoute AI",
    description="AI-assisted digital home healthcare and healthcare accessibility platform",
    version=settings.APP_VERSION,
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        settings.FRONTEND_URL,
        "http://localhost:5173",
        "http://localhost:3000",
        "http://localhost:8000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception: {exc}")
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "message": "An internal server error occurred",
            "error_code": "INTERNAL_ERROR",
        },
    )


# Include routers
from app.routes import auth, patient, health, documents, prescriptions, facilities, emergency, doctor, community, admin  # noqa

app.include_router(auth.router)
app.include_router(patient.router)
app.include_router(health.router)
app.include_router(documents.router)
app.include_router(prescriptions.router)
app.include_router(facilities.router)
app.include_router(emergency.router)
app.include_router(doctor.router)
app.include_router(community.router)
app.include_router(admin.router)


@app.on_event("startup")
async def startup():
    """Initialize database on startup."""
    logger.info("Initializing database...")
    init_db()
    run_light_migrations()
    logger.info("Database initialized.")


@app.get("/")
def root():
    return {
        "name": "CareRoute AI",
        "version": settings.APP_VERSION,
        "description": "AI-assisted digital home healthcare and healthcare accessibility platform",
        "docs": "/docs",
    }


@app.get("/api/health")
def health_check():
    return {"status": "healthy", "service": "CareRoute AI Backend"}
