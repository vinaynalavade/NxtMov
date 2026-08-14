import bcrypt
import hashlib
from datetime import datetime, timedelta, timezone
from typing import Any, Union, Optional
from jose import jwt, JWTError
from app.core.config import settings

def _pre_hash_password(password: str) -> bytes:
    """
    Pre-hash input password using SHA-256 before bcrypt hashing.
    This converts any password of arbitrary length into a fixed 32-byte digest,
    eliminating bcrypt's 72-byte truncation limitation without losing entropy.
    """
    digest = hashlib.sha256(password.encode('utf-8')).hexdigest()
    return digest.encode('utf-8')

def get_password_hash(password: str) -> str:
    pwd_bytes = _pre_hash_password(password)
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(pwd_bytes, salt)
    return hashed.decode('utf-8')

def verify_password(plain_password: str, hashed_password: str) -> bool:
    try:
        pwd_bytes = _pre_hash_password(plain_password)
        hash_bytes = hashed_password.encode('utf-8')
        return bcrypt.checkpw(pwd_bytes, hash_bytes)
    except Exception:
        return False

def create_access_token(
    subject: Union[str, int],
    org_id: int,
    role: str = "ADMIN",
    expires_delta: Optional[timedelta] = None
) -> str:
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode = {
        "exp": int(expire.timestamp()),
        "sub": str(subject),
        "org_id": org_id,
        "role": role,
    }
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt

def decode_access_token(token: str) -> Optional[dict]:
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        return payload
    except JWTError:
        return None
