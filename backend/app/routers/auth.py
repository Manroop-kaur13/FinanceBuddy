"""Registration, login, and logout routes."""

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_session
from app.database.database import get_db
from app.models.user import AuthSession
from app.schemas.user import (
    LoginRequest,
    LogoutResponse,
    TokenResponse,
    UserCreate,
    UserRead,
)
from app.services.auth_service import AuthService

router = APIRouter(prefix="/api/auth", tags=["Authentication"])


@router.post("/register", response_model=UserRead, status_code=status.HTTP_201_CREATED)
def register(user_data: UserCreate, db: Session = Depends(get_db)) -> UserRead:
    """Create a new user; the response never contains the password hash."""
    return AuthService(db).register(user_data)


@router.post("/login", response_model=TokenResponse)
def login(login_data: LoginRequest, db: Session = Depends(get_db)) -> TokenResponse:
    """Verify credentials and return a short-lived bearer access token."""
    token, expires_in = AuthService(db).login(login_data)
    return TokenResponse(access_token=token, expires_in=expires_in)


@router.post("/logout", response_model=LogoutResponse)
def logout(
    auth_session: AuthSession = Depends(get_current_session),
    db: Session = Depends(get_db),
) -> LogoutResponse:
    """Revoke the current login session; the bearer token then stops working."""
    AuthService(db).logout(auth_session)
    return LogoutResponse()
