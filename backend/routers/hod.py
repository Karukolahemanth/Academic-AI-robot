from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from database import get_db
from models.models import HODAvailability, User, HODInfo
from auth import get_current_user, hash_password

router = APIRouter(prefix="/api/hod", tags=["HOD"])

# ── GET /api/hod/availability ─────────────────────────────────────────────────
@router.get("/availability")
def get_availability(db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    record = db.query(HODAvailability).filter(HODAvailability.hod_id == current_user["user_id"]).first()
    if not record:
        raise HTTPException(status_code=404, detail="HOD not found")
    return {
        "hod_id": record.hod_id,
        "is_available": record.is_available,
        "status_message": record.status_message,
        "estimated_return_time": record.estimated_return_time,
        "last_updated": record.last_updated,
    }

class AvailabilityUpdate(BaseModel):
    is_available: bool
    status_message: Optional[str] = None
    estimated_return_time: Optional[datetime] = None

# ── PUT /api/hod/availability ─────────────────────────────────────────────────
@router.put("/availability")
def update_availability(payload: AvailabilityUpdate, db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    record = db.query(HODAvailability).filter(HODAvailability.hod_id == current_user["user_id"]).first()
    if not record:
        raise HTTPException(status_code=404, detail="HOD not found")
    record.is_available = payload.is_available
    if payload.status_message is not None:
        record.status_message = payload.status_message
    if payload.estimated_return_time is not None:
        record.estimated_return_time = payload.estimated_return_time
    record.last_updated = datetime.utcnow()
    db.commit()
    return {"message": "Availability updated successfully"}

# ── GET /api/hod/profile ──────────────────────────────────────────────────────
@router.get("/profile")
def get_hod_profile(db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    hod = db.query(User).filter(User.user_id == current_user["user_id"]).first()
    if not hod:
        raise HTTPException(status_code=404, detail="HOD not found")
    info = db.query(HODInfo).filter(HODInfo.hod_id == hod.user_id).first()
    return {
        "user_id": hod.user_id, "name": hod.name, "email": hod.email, "role": hod.role,
        "hod_info": {"department": info.department if info else None,
                     "office_room": info.office_room if info else None,
                     "contact_number": info.contact_number if info else None}
    }

class HODProfileUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None
    password: Optional[str] = None
    contact_number: Optional[str] = None
    office_room: Optional[str] = None

# ── PUT /api/hod/profile ──────────────────────────────────────────────────────
@router.put("/profile")
def update_hod_profile(payload: HODProfileUpdate, db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    hod = db.query(User).filter(User.user_id == current_user["user_id"]).first()
    if not hod:
        raise HTTPException(status_code=404, detail="HOD not found")
    if payload.name:  hod.name = payload.name
    if payload.email: hod.email = payload.email
    if payload.password: hod.password_hash = hash_password(payload.password)
    db.commit()
    info = db.query(HODInfo).filter(HODInfo.hod_id == hod.user_id).first()
    if info:
        if payload.contact_number: info.contact_number = payload.contact_number
        if payload.office_room:    info.office_room = payload.office_room
        db.commit()
    return {"message": "Profile updated successfully"}
