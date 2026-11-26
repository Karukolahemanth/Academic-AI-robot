from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr
from database import get_db
from models.models import User, HODAvailability
from auth import hash_password, verify_password, create_access_token

router = APIRouter(prefix="/api/auth", tags=["Auth"])

# ── Schemas ───────────────────────────────────────────────────────────────────
class SignupRequest(BaseModel):
    name: str
    email: str
    password: str
    role: str   # HOD | Proctor

class LoginRequest(BaseModel):
    email: str
    password: str

# ── POST /api/auth/signup ─────────────────────────────────────────────────────
@router.post("/signup", status_code=201)
def signup(payload: SignupRequest, db: Session = Depends(get_db)):
    if db.query(User).filter(User.email == payload.email).first():
        raise HTTPException(status_code=409, detail="Error: Email already in use.")

    user = User(
        name=payload.name,
        email=payload.email,
        password_hash=hash_password(payload.password),
        role=payload.role,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    # Auto-create HOD availability record
    if payload.role == "HOD":
        db.add(HODAvailability(
            hod_id=user.user_id,
            is_available=False,
            status_message="HOD status not yet updated."
        ))
        db.commit()

    return {"message": "User registered successfully!", "userId": user.user_id, "role": user.role}


# ── POST /api/auth/login ──────────────────────────────────────────────────────
@router.post("/login")
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == payload.email).first()
    if not user:
        raise HTTPException(status_code=404, detail="Authentication failed. User not found.")

    if not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Authentication failed. Invalid password.")

    token = create_access_token(user.user_id, user.role)
    return {
        "message": "Login successful.",
        "accessToken": token,
        "user": {"id": user.user_id, "name": user.name, "email": user.email, "role": user.role},
    }
