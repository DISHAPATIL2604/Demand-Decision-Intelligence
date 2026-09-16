from datetime import datetime, timedelta, timezone
from typing import Optional, Any
from backend.core.config import settings

try:
    from passlib.context import CryptContext
    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        return pwd_context.verify(plain_password, hashed_password)
    def get_password_hash(password: str) -> str:
        return pwd_context.hash(password)
except ImportError:
    import hashlib
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        return get_password_hash(plain_password) == hashed_password
    def get_password_hash(password: str) -> str:
        return hashlib.sha256(password.encode()).hexdigest()

try:
    from jose import jwt
except ImportError:
    import json, base64
    class MockJWT:
        @staticmethod
        def encode(claims, key, algorithm="HS256"):
            return base64.urlsafe_b64encode(json.dumps(claims, default=str).encode()).decode()
    jwt = MockJWT()

def create_access_token(subject: str | Any, expires_delta: Optional[timedelta] = None) -> str:
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode = {"exp": expire, "sub": str(subject)}
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
