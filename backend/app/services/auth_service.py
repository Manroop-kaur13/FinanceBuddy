"""Registration, password authentication, and login-session operations."""

from datetime import UTC, datetime, timedelta
from uuid import uuid4

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.security import create_access_token, verify_password
from app.models.user import AuthSession, User
from app.schemas.user import LoginRequest, UserCreate
from app.services.user_service import UserService


class AuthService:
    """Encapsulate authentication and revocable token-session behavior."""

    def __init__(self, db: Session) -> None:
        self.db = db
        self.users = UserService(db)

    def register(self, user_data: UserCreate) -> User:
        """Create a new account through the user service."""
        return self.users.register(user_data)

    def authenticate(self, login_data: LoginRequest) -> User | None:
        """Verify the submitted password without revealing whether email exists."""
        user = self.users.get_by_email(str(login_data.email))
        if user is None or not verify_password(login_data.password, user.hashed_password):
            return None
        return user

    def login(self, login_data: LoginRequest) -> tuple[str, int]:
        """Authenticate the user, persist a session, and return its signed token."""
        user = self.authenticate(login_data)
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Email or password is incorrect.",
                headers={"WWW-Authenticate": "Bearer"},
            )

        settings = get_settings()
        expires_in = settings.access_token_expire_minutes * 60
        expires_at = datetime.now(UTC) + timedelta(seconds=expires_in)
        session = AuthSession(
            id=uuid4(),
            user_id=user.id,
            expires_at=expires_at,
        )
        token = create_access_token(
            user_id=user.id,
            session_id=session.id,
            expires_at=expires_at,
        )
        self.db.add(session)
        self.db.commit()
        return token, expires_in

    def logout(self, auth_session: AuthSession) -> None:
        """Revoke this token's database session so it cannot be reused."""
        auth_session.revoked_at = datetime.now(UTC)
        self.db.commit()

