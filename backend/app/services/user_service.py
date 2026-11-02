"""Business operations for user profiles and account ownership."""

from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.user import User
from app.schemas.user import UserCreate, UserUpdate
from app.core.security import hash_password


class UserService:
    """Encapsulate database operations that manage user records."""

    def __init__(self, db: Session) -> None:
        self.db = db

    @staticmethod
    def normalize_email(email: str) -> str:
        """Store email addresses in a consistent lowercase form."""
        return email.strip().lower()

    def get_by_email(self, email: str) -> User | None:
        """Look up a user by normalized email address."""
        normalized_email = self.normalize_email(email)
        return self.db.scalar(select(User).where(User.email == normalized_email))

    def get_by_id(self, user_id: UUID) -> User | None:
        """Look up a user by their database ID."""
        return self.db.get(User, user_id)

    def register(self, user_data: UserCreate) -> User:
        """Create a user with a one-way Argon2 password hash."""
        email = self.normalize_email(str(user_data.email))
        if self.get_by_email(email) is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="An account with this email already exists.",
            )

        user = User(
            name=user_data.name,
            email=email,
            hashed_password=hash_password(user_data.password),
        )
        self.db.add(user)
        try:
            self.db.commit()
        except IntegrityError as exc:
            self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="An account with this email already exists.",
            ) from exc
        self.db.refresh(user)
        return user

    def update_profile(self, user: User, updates: UserUpdate) -> User:
        """Update the current user's name or email address."""
        values = updates.model_dump(exclude_unset=True)
        if "name" in values:
            user.name = values["name"]
        if "email" in values and values["email"] is not None:
            normalized_email = self.normalize_email(str(values["email"]))
            existing = self.get_by_email(normalized_email)
            if existing is not None and existing.id != user.id:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="An account with this email already exists.",
                )
            user.email = normalized_email

        try:
            self.db.commit()
        except IntegrityError as exc:
            self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="An account with this email already exists.",
            ) from exc
        self.db.refresh(user)
        return user

    def delete_account(self, user: User) -> None:
        """Delete the user and cascade to their sessions and future owned data."""
        self.db.delete(user)
        self.db.commit()
