"""Dependencies shared by protected API routes."""

from datetime import UTC, datetime
from uuid import UUID

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.core.security import decode_access_token
from app.database.database import get_db
from app.models.user import AuthSession, User

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")


def _unauthorized() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or expired access token.",
        headers={"WWW-Authenticate": "Bearer"},
    )


def get_current_session(
    token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)
) -> AuthSession:
    """Resolve a valid bearer token to an active, non-revoked database session."""
    claims = decode_access_token(token)
    try:
        user_id = UUID(str(claims["sub"]))
        session_id = UUID(str(claims["jti"]))
    except (KeyError, ValueError, TypeError) as exc:
        raise _unauthorized() from exc

    auth_session = db.scalar(
        select(AuthSession)
        .options(joinedload(AuthSession.user))
        .where(AuthSession.id == session_id, AuthSession.user_id == user_id)
    )
    if (
        auth_session is None
        or auth_session.revoked_at is not None
        or (auth_session.expires_at.replace(tzinfo=UTC) if auth_session.expires_at.tzinfo is None else auth_session.expires_at) <= datetime.now(UTC)
    ):
        raise _unauthorized()
    return auth_session


def get_current_user(
    auth_session: AuthSession = Depends(get_current_session),
) -> User:
    """Return the user associated with the verified access token."""
    return auth_session.user
