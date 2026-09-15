"""
Document upload and management routes.
"""
import os
import uuid
from datetime import date
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
from typing import Optional

from app.db.database import get_db
from app.models.user import User
from app.models.patient import PatientProfile
from app.models.document import MedicalDocument
from app.core.auth import get_current_user_id
from app.core.config import get_settings

settings = get_settings()
router = APIRouter(prefix="/api/documents", tags=["Documents"])

ALLOWED_TYPES = {"pdf", "jpg", "jpeg", "png", "doc", "docx", "txt"}
MAX_SIZE = settings.MAX_FILE_SIZE_MB * 1024 * 1024


@router.post("/upload", status_code=201)
async def upload_document(
    file: UploadFile = File(...),
    title: str = Form(""),
    document_type: str = Form("other"),
    doctor_name: str = Form(""),
    facility_name: str = Form(""),
    document_date: str = Form(""),
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """Upload a medical document."""
    profile = db.query(PatientProfile).filter(PatientProfile.user_id == user_id).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Patient profile not found")
    
    # Validate file
    ext = file.filename.split(".")[-1].lower() if file.filename else ""
    if ext not in ALLOWED_TYPES:
        raise HTTPException(status_code=400, detail=f"File type '{ext}' not allowed. Allowed: {', '.join(ALLOWED_TYPES)}")
    
    # Check file size
    content = await file.read()
    if len(content) > MAX_SIZE:
        raise HTTPException(status_code=400, detail=f"File too large. Maximum size: {settings.MAX_FILE_SIZE_MB}MB")
    
    # Save file
    upload_dir = os.path.join(settings.UPLOAD_DIR, str(user_id))
    os.makedirs(upload_dir, exist_ok=True)
    
    filename = f"{uuid.uuid4().hex}.{ext}"
    filepath = os.path.join(upload_dir, filename)
    
    with open(filepath, "wb") as f:
        f.write(content)
    
    # Parse date
    doc_date = None
    if document_date:
        try:
            doc_date = date.fromisoformat(document_date)
        except ValueError:
            pass
    
    # Create document record
    doc = MedicalDocument(
        patient_id=profile.id,
        uploaded_by=user_id,
        title=title or file.filename or "Untitled Document",
        document_type=document_type,
        file_path=filepath,
        file_size=len(content),
        mime_type=file.content_type,
        doctor_name=doctor_name or None,
        facility_name=facility_name or None,
        document_date=doc_date,
    )
    db.add(doc)
    db.commit()
    db.refresh(doc)
    
    return {
        "id": doc.id,
        "title": doc.title,
        "document_type": doc.document_type,
        "file_size": doc.file_size,
        "message": "Document uploaded successfully",
    }


@router.get("/")
def list_documents(
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """List user's medical documents."""
    profile = db.query(PatientProfile).filter(PatientProfile.user_id == user_id).first()
    if not profile:
        return {"documents": []}
    
    docs = db.query(MedicalDocument).filter(
        MedicalDocument.patient_id == profile.id
    ).order_by(MedicalDocument.created_at.desc()).all()
    
    return {
        "documents": [
            {
                "id": d.id,
                "title": d.title,
                "document_type": d.document_type,
                "file_size": d.file_size,
                "doctor_name": d.doctor_name,
                "facility_name": d.facility_name,
                "document_date": str(d.document_date) if d.document_date else None,
                "created_at": str(d.created_at) if d.created_at else None,
            }
            for d in docs
        ]
    }


@router.get("/{document_id}")
def get_document(
    document_id: int,
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """Get document details."""
    profile = db.query(PatientProfile).filter(PatientProfile.user_id == user_id).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Patient profile not found")
    
    doc = db.query(MedicalDocument).filter(
        MedicalDocument.id == document_id,
        MedicalDocument.patient_id == profile.id,
    ).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    
    return {
        "id": doc.id,
        "title": doc.title,
        "document_type": doc.document_type,
        "file_size": doc.file_size,
        "mime_type": doc.mime_type,
        "doctor_name": doc.doctor_name,
        "facility_name": doc.facility_name,
        "document_date": str(doc.document_date) if doc.document_date else None,
        "extracted_data": doc.extracted_data,
        "created_at": str(doc.created_at) if doc.created_at else None,
    }


@router.delete("/{document_id}")
def delete_document(
    document_id: int,
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """Delete a document."""
    profile = db.query(PatientProfile).filter(PatientProfile.user_id == user_id).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Patient profile not found")
    
    doc = db.query(MedicalDocument).filter(
        MedicalDocument.id == document_id,
        MedicalDocument.patient_id == profile.id,
    ).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    
    # Remove file
    if doc.file_path and os.path.exists(doc.file_path):
        os.remove(doc.file_path)
    
    db.delete(doc)
    db.commit()
    return {"message": "Document deleted"}
