"""Password hashing and JWT access-token helpers."""

from datetime import UTC, datetime, timedelta
from uuid import UUID

import jwt
from fastapi import HTTPException, status
from pwdlib import PasswordHash

from app.core.config import get_settings

password_hasher = PasswordHash.recommended()


def hash_password(password: str) -> str:
    """Return a one-way Argon2 password hash suitable for database storage."""
    return password_hasher.hash(password)


def verify_password(password: str, hashed_password: str) -> bool:
    """Check a password against its stored one-way hash."""
    return password_hasher.verify(password, hashed_password)


def _jwt_secret() -> str:
    secret = get_settings().jwt_secret_key
    if not secret:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Authentication is not configured. Set JWT_SECRET_KEY in backend/.env.",
        )
    return secret


def create_access_token(
    *, user_id: UUID, session_id: UUID, expires_at: datetime
) -> str:
    """Sign a short-lived token tied to a revocable database session."""
    now = datetime.now(UTC)
    payload = {
        "sub": str(user_id),
        "jti": str(session_id),
        "iat": now,
        "exp": expires_at,
    }
    settings = get_settings()
    return jwt.encode(payload, _jwt_secret(), algorithm=settings.jwt_algorithm)


def decode_access_token(token: str) -> dict[str, object]:
    """Validate token signature and expiry, returning its claims."""
    settings = get_settings()
    try:
        return jwt.decode(
            token,
            _jwt_secret(),
            algorithms=[settings.jwt_algorithm],
            options={"require": ["sub", "jti", "iat", "exp"]},
        )
    except jwt.PyJWTError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired access token.",
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc
