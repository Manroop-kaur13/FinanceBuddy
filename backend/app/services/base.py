"""Shared helpers for user-scoped service classes."""

from typing import Any, TypeVar
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database.base import Base

ModelType = TypeVar("ModelType", bound=Base)


class OwnedService:
    """Base for services that only access rows owned by the signed-in user."""

    model: type[ModelType]

    def __init__(self, db: Session, user_id: UUID) -> None:
        self.db = db
        self.user_id = user_id

    def get_owned(self, item_id: UUID) -> ModelType:
        item = self.db.scalar(
            select(self.model).where(
                self.model.id == item_id,  # type: ignore[attr-defined]
                self.model.user_id == self.user_id,  # type: ignore[attr-defined]
            )
        )
        if item is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Record not found.")
        return item

    def list_owned(self, *, limit: int = 100, offset: int = 0) -> list[ModelType]:
        return list(
            self.db.scalars(
                select(self.model)  # type: ignore[arg-type]
                .where(self.model.user_id == self.user_id)  # type: ignore[attr-defined]
                .order_by(self.model.id)  # type: ignore[attr-defined]
                .limit(limit)
                .offset(offset)
            ).all()
        )

    @staticmethod
    def apply_updates(item: Any, updates: Any) -> Any:
        for name, value in updates.model_dump(exclude_unset=True).items():
            setattr(item, name, value)
        return item
