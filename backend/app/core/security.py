from datetime import datetime, timedelta, timezone
from jose import jwt, JWTError
from base64 import b64decode, b64encode
from hashlib import pbkdf2_hmac
from hmac import compare_digest
from secrets import token_bytes
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from .config import settings
from .database import get_db

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")
def hash_password(value: str) -> str:
    """PBKDF2-SHA256 password hash; the salt and iteration count travel with the hash."""
    salt = token_bytes(16)
    rounds = 600_000
    derived = pbkdf2_hmac("sha256", value.encode(), salt, rounds)
    return f"pbkdf2_sha256${rounds}${b64encode(salt).decode()}${b64encode(derived).decode()}"
def verify_password(value: str, hashed: str) -> bool:
    try:
        algorithm, rounds, salt, expected = hashed.split("$", 3)
        if algorithm != "pbkdf2_sha256": return False
        actual = pbkdf2_hmac("sha256", value.encode(), b64decode(salt), int(rounds))
        return compare_digest(actual, b64decode(expected))
    except (ValueError, TypeError):
        return False
def create_token(subject, role):
    return jwt.encode({"sub": str(subject), "role": role, "exp": datetime.now(timezone.utc) + timedelta(minutes=settings.token_minutes)}, settings.secret_key, algorithm="HS256")
def current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    from app.models.models import User
    try: user_id = int(jwt.decode(token, settings.secret_key, algorithms=["HS256"])["sub"])
    except (JWTError, KeyError, ValueError): raise HTTPException(status_code=401, detail="Invalid or expired token")
    user = db.get(User, user_id)
    if not user or not user.active: raise HTTPException(status_code=401, detail="Account unavailable")
    return user
def require_roles(*roles):
    def guard(user=Depends(current_user)):
        if user.role not in roles: raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions")
        return user
    return guard
