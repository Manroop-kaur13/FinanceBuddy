"""CRUD for recurring transaction schedules."""

from uuid import UUID

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.account import Account
from app.models.recurring_transaction import RecurringTransaction
from app.schemas.recurring_transaction import RecurringTransactionCreate, RecurringTransactionUpdate
from app.services.base import OwnedService


class RecurringTransactionService(OwnedService):
    """Store schedules; a background worker can execute them in a later phase."""

    model = RecurringTransaction

    def __init__(self, db: Session, user_id: UUID) -> None:
        super().__init__(db, user_id)

    def _check_account(self, account_id: UUID) -> None:
        if self.db.scalar(
            select(Account.id).where(Account.id == account_id, Account.user_id == self.user_id)
        ) is None:
            raise HTTPException(status_code=404, detail="Account not found.")

    def create_schedule(self, data: RecurringTransactionCreate) -> RecurringTransaction:
        self._check_account(data.account_id)
        item = RecurringTransaction(user_id=self.user_id, **data.model_dump())
        self.db.add(item)
        self.db.commit()
        self.db.refresh(item)
        return item

    def get_schedules(self, *, limit: int = 100, offset: int = 0) -> list[RecurringTransaction]:
        return self.list_owned(limit=limit, offset=offset)

    def update_schedule(self, item_id: UUID, data: RecurringTransactionUpdate) -> RecurringTransaction:
        item = self.get_owned(item_id)
        values = data.model_dump(exclude_unset=True)
        if values.get("account_id") is not None:
            self._check_account(values["account_id"])
        for field, value in values.items():
            if value is not None:
                setattr(item, field, value)
        self.db.commit()
        self.db.refresh(item)
        return item

    def delete_schedule(self, item_id: UUID) -> None:
        self.db.delete(self.get_owned(item_id))
        self.db.commit()
