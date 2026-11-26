from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
from database import get_db
from models.models import VisitLog, HODAvailability, StudentCore

router = APIRouter(prefix="/api/bot", tags=["Kiosk Bot"])

class VisitCreate(BaseModel):
    role: str
    name: str
    contact: str
    student_id: Optional[str] = None
    purpose: str

# ── GET /api/bot/status — HOD availability for the kiosk ─────────────────────
@router.get("/status")
def get_kiosk_status(db: Session = Depends(get_db)):
    availability = db.query(HODAvailability).filter(HODAvailability.hod_id == 2).first()
    if not availability:
        return {"is_available": False, "status_message": "Status unavailable", "estimated_return_time": None}
    return {
        "is_available": availability.is_available,
        "status_message": availability.status_message,
        "estimated_return_time": availability.estimated_return_time,
    }

# ── POST /api/bot/log-visit — Raspberry Pi kiosk submits visitor ──────────────
@router.post("/log-visit", status_code=201)
def log_visit(payload: VisitCreate, db: Session = Depends(get_db)):
    if not all([payload.role, payload.name, payload.contact, payload.purpose]):
        raise HTTPException(status_code=400, detail="Role, Name, Contact, and Purpose are required.")

    related_student_db_id = None
    normalized = payload.role.lower()
    if normalized in ("parent", "student"):
        if not payload.student_id:
            raise HTTPException(status_code=400, detail="Student Roll Number is required for Parents and Students.")
        student_roll = str(payload.student_id).strip().upper()
        student = db.query(StudentCore).filter(StudentCore.roll_number == student_roll).first()
        if not student:
            raise HTTPException(status_code=404, detail=f"Student with roll number '{student_roll}' not found.")
        related_student_db_id = student.student_id

    # Check HOD availability
    hod_status = db.query(HODAvailability).filter(HODAvailability.hod_id == 2).first()

    visit = VisitLog(
        visitor_name=payload.name,
        visitor_role=payload.role,
        related_student_id=related_student_db_id,
        purpose=payload.purpose,
        status="Queued",
        action_taken="Pending",
        alert_sent=False,
    )
    db.add(visit)
    db.commit()
    db.refresh(visit)

    return {
        "message": "Visit logged successfully",
        "hod_available": hod_status.is_available if hod_status else False,
        "status_message": hod_status.status_message if hod_status else "Currently unavailable",
        "estimated_return_time": hod_status.estimated_return_time if hod_status else None,
        "visit_id": visit.visit_id,
    }
