from app.schemas.base import APIModel
"""Validation and response schemas for user and authentication endpoints."""

from datetime import datetime
from uuid import UUID

from pydantic import ConfigDict, EmailStr, Field, model_validator


class UserCreate(APIModel):
    """Fields accepted when registering a new user."""

    name: str = Field(min_length=1, max_length=120)
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)


class LoginRequest(APIModel):
    """Email and password submitted to start a login session."""

    email: EmailStr
    password: str = Field(min_length=1, max_length=128)


class UserUpdate(APIModel):
    """Optional profile fields that can be changed by the signed-in user."""

    name: str | None = Field(default=None, min_length=1, max_length=120)
    email: EmailStr | None = None

    @model_validator(mode="after")
    def require_at_least_one_change(self) -> "UserUpdate":
        if self.name is None and self.email is None:
            raise ValueError("Provide a name or email address to update.")
        return self


class DeleteAccountRequest(APIModel):
    """Require the user's current password before deleting the account."""

    password: str = Field(min_length=1, max_length=128)


class UserRead(APIModel):
    """Public user fields; password hashes are never included."""

    id: UUID
    name: str
    email: EmailStr
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class TokenResponse(APIModel):
    """Short-lived bearer token returned after a successful login."""

    access_token: str
    token_type: str = "bearer"
    expires_in: int


class LogoutResponse(APIModel):
    """Confirmation returned after revoking the active login session."""

    message: str = "Logged out successfully."
