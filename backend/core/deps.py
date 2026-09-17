"""
FastAPI reusable dependencies.
Import get_current_user in any route that requires authentication.
"""
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from backend.db.session import get_db
from backend.core.security import decode_access_token
from backend.models.user import User

# Tells FastAPI where clients send the token (used for /api/docs OAuth2 flow)
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")


def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> User:
    """
    Decode the Bearer JWT, look up the user in the database and return them.
    Raises HTTP 401 if the token is missing, expired, or the user no longer exists.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    subject = decode_access_token(token)
    if subject is None:
        raise credentials_exception

    # Subject is stored as the user's email
    user = db.query(User).filter(User.email == subject).first()
    if user is None:
        # Fallback: try matching by username (legacy tokens)
        user = db.query(User).filter(User.username == subject).first()

    if user is None:
        raise credentials_exception

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user account",
        )

    return user


def get_current_active_user(
    current_user: User = Depends(get_current_user),
) -> User:
    """Alias kept for explicit intent in route signatures."""
    return current_user
