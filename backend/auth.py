import bcrypt
from datetime import datetime, timedelta
from jose import JWTError, jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from dotenv import load_dotenv
import os

load_dotenv()

JWT_SECRET = os.getenv("JWT_SECRET", "asdfghjkmnbvcxwertyuiovcxcvbn")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_HOURS = 8

bearer_scheme = HTTPBearer()

# ── Password helpers ──────────────────────────────────────────────────────────
def hash_password(password: str) -> str:
    pw_bytes = password.encode("utf-8")[:72]
    return bcrypt.hashpw(pw_bytes, bcrypt.gensalt()).decode("utf-8")

def verify_password(plain: str, hashed: str) -> bool:
    pw_bytes = plain.encode("utf-8")[:72]
    return bcrypt.checkpw(pw_bytes, hashed.encode("utf-8"))

# ── JWT helpers ───────────────────────────────────────────────────────────────
def create_access_token(user_id: int, role: str) -> str:
    expire = datetime.utcnow() + timedelta(hours=ACCESS_TOKEN_EXPIRE_HOURS)
    payload = {"id": user_id, "role": role, "exp": expire}
    return jwt.encode(payload, JWT_SECRET, algorithm=ALGORITHM)

def decode_token(token: str) -> dict:
    try:
        return jwt.decode(token, JWT_SECRET, algorithms=[ALGORITHM])
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Failed to authenticate token"
        )

# ── Dependency: current user from Bearer token ────────────────────────────────
def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme)
) -> dict:
    token = credentials.credentials
    payload = decode_token(token)
    return {"user_id": payload["id"], "role": payload["role"]}

def require_hod(current_user: dict = Depends(get_current_user)) -> dict:
    if current_user["role"] != "HOD":
        raise HTTPException(status_code=403, detail="HOD access only")
    return current_user

def require_proctor(current_user: dict = Depends(get_current_user)) -> dict:
    if current_user["role"] != "Proctor":
        raise HTTPException(status_code=403, detail="Proctor access only")
    return current_user
