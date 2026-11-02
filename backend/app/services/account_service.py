"""User-scoped account CRUD operations."""

from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.account import Account
from app.models.credit_card import CreditCard
from app.models.transaction import Transaction
from app.schemas.account import AccountCreate, AccountUpdate
from app.services.base import OwnedService


class AccountService(OwnedService):
    """Create and manage accounts without allowing cross-user access."""

    model = Account

    def __init__(self, db: Session, user_id: UUID) -> None:
        super().__init__(db, user_id)

    def create_account(self, data: AccountCreate) -> Account:
        account = Account(
            user_id=self.user_id,
            account_name=data.account_name,
            account_type=data.account_type,
            currency=data.currency,
            opening_balance=data.opening_balance,
            current_balance=data.opening_balance,
        )
        self.db.add(account)
        self.db.commit()
        self.db.refresh(account)
        return account

    def get_accounts(self, *, limit: int = 100, offset: int = 0) -> list[Account]:
        return self.list_owned(limit=limit, offset=offset)

    def get_account(self, account_id: UUID) -> Account:
        return self.get_owned(account_id)

    def update_account(self, account_id: UUID, data: AccountUpdate) -> Account:
        account = self.get_owned(account_id)
        self.apply_updates(account, data)
        self.db.commit()
        self.db.refresh(account)
        return account

    def delete_account(self, account_id: UUID) -> None:
        account = self.get_owned(account_id)
        has_transactions = self.db.scalar(
            select(Transaction.id).where(
                (Transaction.account_id == account_id)
                | (Transaction.destination_account_id == account_id)
            ).limit(1)
        )
        has_card = self.db.scalar(
            select(CreditCard.id).where(CreditCard.account_id == account_id).limit(1)
        )
        if has_transactions or has_card:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Account has transaction history or a linked credit card and cannot be deleted.",
            )
        self.db.delete(account)
        self.db.commit()

    def get_account_balance(self, account_id: UUID):
        return self.get_owned(account_id).current_balance
