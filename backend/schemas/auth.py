from pydantic import BaseModel, field_validator
from typing import Optional

try:
    import email_validator  # noqa: F401
    from pydantic import EmailStr
except ImportError:
    EmailStr = str  # type: ignore


# ──────────────────────────────────────────────
# Token schemas
# ──────────────────────────────────────────────

class Token(BaseModel):
    access_token: str
    token_type: str


class TokenPayload(BaseModel):
    sub: Optional[str] = None


# ──────────────────────────────────────────────
# Login / OAuth2 form schema
# ──────────────────────────────────────────────

class LoginRequest(BaseModel):
    """Accepts either email or username in the `username` field."""
    username: str
    password: str


# ──────────────────────────────────────────────
# Registration schemas
# ──────────────────────────────────────────────

class UserRegister(BaseModel):
    email: EmailStr
    username: str
    password: str
    full_name: Optional[str] = None

    @field_validator("password")
    @classmethod
    def password_strength(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters.")
        return v

    @field_validator("username")
    @classmethod
    def username_alphanumeric(cls, v: str) -> str:
        v = v.strip()
        if len(v) < 3:
            raise ValueError("Username must be at least 3 characters.")
        return v


# ──────────────────────────────────────────────
# Response schemas
# ──────────────────────────────────────────────

class UserResponse(BaseModel):
    id: int
    email: str
    username: str
    full_name: Optional[str] = None
    role: str          # resolved from relationship
    is_active: bool

    class Config:
        from_attributes = True