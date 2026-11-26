from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import asc, desc
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from database import get_db
from models.models import VisitLog
from auth import get_current_user

router = APIRouter(prefix="/api/visit_logs", tags=["Visit Logs"])

VALID_TRANSITIONS = {
    "Pending":   ["Scheduled", "Completed", "Cancelled"],
    "Scheduled": ["Scheduled", "Completed", "Cancelled"],
    "Completed": [],
    "Cancelled": [],
}

def _fmt(v: VisitLog) -> dict:
    return {
        "visit_id": v.visit_id, "visitor_name": v.visitor_name,
        "visitor_role": v.visitor_role, "purpose": v.purpose,
        "status": v.status, "action_taken": v.action_taken,
        "check_in_time": v.check_in_time, "scheduled_time": v.scheduled_time,
        "hod_notes": v.hod_notes, "end_time": v.end_time,
        "related_student_id": v.related_student_id,
        "related_student_roll": v.student.roll_number if v.student else None,
        "student_name": v.student.full_name if v.student else None,
    }

# ── GET /api/visit_logs/ — all ────────────────────────────────────────────────
@router.get("/")
@router.get("", include_in_schema=False)
def get_all(db: Session = Depends(get_db), _=Depends(get_current_user)):
    visits = db.query(VisitLog).options(joinedload(VisitLog.student)).order_by(desc(VisitLog.check_in_time)).all()
    return [_fmt(v) for v in visits]

# ── GET /api/visit_logs/queued ────────────────────────────────────────────────
@router.get("/queued")
def get_queued(db: Session = Depends(get_db), _=Depends(get_current_user)):
    visits = db.query(VisitLog).options(joinedload(VisitLog.student)).filter(VisitLog.status == "Queued").order_by(asc(VisitLog.check_in_time)).all()
    return [_fmt(v) for v in visits]

# ── PUT /api/visit_logs/acknowledge-new ───────────────────────────────────────
@router.put("/acknowledge-new")
def acknowledge_new(db: Session = Depends(get_db), _=Depends(get_current_user)):
    count = db.query(VisitLog).filter(VisitLog.status == "Queued").update({"status": "Pending"})
    db.commit()
    return {"message": f"{count} new requests acknowledged."}

# ── GET /api/visit_logs/pending ───────────────────────────────────────────────
@router.get("/pending")
def get_pending(db: Session = Depends(get_db), _=Depends(get_current_user)):
    visits = db.query(VisitLog).options(joinedload(VisitLog.student)).filter(VisitLog.action_taken == "Pending").order_by(asc(VisitLog.check_in_time)).all()
    return [_fmt(v) for v in visits]

# ── GET /api/visit_logs/scheduled ────────────────────────────────────────────
@router.get("/scheduled")
def get_scheduled(db: Session = Depends(get_db), _=Depends(get_current_user)):
    visits = db.query(VisitLog).options(joinedload(VisitLog.student)).filter(VisitLog.action_taken == "Scheduled").order_by(asc(VisitLog.scheduled_time)).all()
    return [_fmt(v) for v in visits]

# ── GET /api/visit_logs/history ───────────────────────────────────────────────
@router.get("/history")
def get_history(db: Session = Depends(get_db)):
    visits = db.query(VisitLog).options(joinedload(VisitLog.student)).filter(VisitLog.action_taken == "Completed").order_by(desc(VisitLog.check_in_time)).all()
    return [_fmt(v) for v in visits]

class StatusUpdate(BaseModel):
    action_taken: str
    scheduled_time: Optional[datetime] = None
    hod_notes: Optional[str] = None

# ── PUT /api/visit_logs/{id}/update-status ────────────────────────────────────
@router.put("/{visit_id}/update-status")
def update_status(visit_id: int, payload: StatusUpdate, db: Session = Depends(get_db), _=Depends(get_current_user)):
    visit = db.query(VisitLog).filter(VisitLog.visit_id == visit_id).first()
    if not visit:
        raise HTTPException(status_code=404, detail="Appointment not found")

    current = visit.action_taken or "Pending"
    allowed = VALID_TRANSITIONS.get(current, [])
    if payload.action_taken not in allowed:
        raise HTTPException(status_code=400, detail=f"Cannot change {current} to {payload.action_taken}")

    if payload.action_taken == "Scheduled" and payload.scheduled_time:
        visit.scheduled_time = payload.scheduled_time
    if payload.action_taken == "Completed":
        visit.status = "CheckedIn"
        visit.end_time = datetime.utcnow()
        if payload.hod_notes:
            visit.hod_notes = payload.hod_notes

    visit.action_taken = payload.action_taken
    db.commit()
    return {"message": "Appointment updated successfully", "visit": _fmt(visit)}
