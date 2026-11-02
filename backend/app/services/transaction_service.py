"""Atomic income, expense, and transfer processing."""

from datetime import date
from decimal import Decimal
from typing import Literal
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.account import Account
from app.models.bill import Bill
from app.models.loan import LoanPayment
from app.models.transaction import Transaction
from app.schemas.transaction import TransactionCreate


class TransactionService:
    """Keep transaction history and account balances consistent."""

    def __init__(self, db: Session, user_id: UUID) -> None:
        self.db = db
        self.user_id = user_id

    def _get_account(self, account_id: UUID) -> Account:
        account = self.db.scalar(
            select(Account).where(Account.id == account_id, Account.user_id == self.user_id)
        )
        if account is None:
            raise HTTPException(status_code=404, detail="Account not found.")
        return account

    def _validate_accounts(self, data: TransactionCreate) -> tuple[Account, Account | None]:
        source = self._get_account(data.account_id)
        destination = None
        if data.transaction_type == "transfer":
            if data.destination_account_id is None:
                raise HTTPException(status_code=422, detail="Transfer destination is required.")
            destination = self._get_account(data.destination_account_id)
            if source.currency != destination.currency:
                raise HTTPException(
                    status_code=422,
                    detail="Transfers between different currencies are not supported.",
                )
        return source, destination

    def _apply_balance(self, transaction: Transaction, direction: int) -> None:
        amount = Decimal(transaction.amount) * direction
        source = self._get_account(transaction.account_id)
        if transaction.transaction_type == "income":
            source.current_balance += amount
        elif transaction.transaction_type == "expense":
            source.current_balance -= amount
        elif transaction.transaction_type == "transfer":
            if transaction.destination_account_id is None:
                raise HTTPException(status_code=422, detail="Transfer destination is required.")
            destination = self._get_account(transaction.destination_account_id)
            source.current_balance -= amount
            destination.current_balance += amount

    @staticmethod
    def _copy_fields(transaction: Transaction, data: TransactionCreate) -> None:
        transaction.account_id = data.account_id
        transaction.destination_account_id = data.destination_account_id
        transaction.transaction_type = data.transaction_type
        transaction.amount = data.amount
        transaction.category = data.category
        transaction.description = data.description
        transaction.transaction_date = data.transaction_date
        transaction.merchant = data.merchant
        transaction.notes = data.notes

    def add_transaction(
        self,
        data: TransactionCreate,
        *,
        commit: bool = True,
        internal_card_operation: bool = False,
    ) -> Transaction:
        source, destination = self._validate_accounts(data)
        if not internal_card_operation and self._is_credit_card_account(source.id):
            raise HTTPException(
                status_code=409,
                detail="Use the credit-card expense endpoint for card purchases.",
            )
        if (
            not internal_card_operation
            and destination is not None
            and self._is_credit_card_account(destination.id)
        ):
            raise HTTPException(
                status_code=409,
                detail="Use the credit-card payment endpoint to pay a card.",
            )
        transaction = Transaction(user_id=self.user_id, **data.model_dump())
        try:
            self._apply_balance(transaction, 1)
            self.db.add(transaction)
            self.db.flush()
            if commit:
                self.db.commit()
                self.db.refresh(transaction)
        except Exception:
            self.db.rollback()
            raise
        return transaction

    def _is_credit_card_account(self, account_id: UUID) -> bool:
        return self.db.scalar(
            select(Account.id).where(
                Account.id == account_id,
                Account.user_id == self.user_id,
                Account.account_type == "credit_card",
            ).limit(1)
        ) is not None

    def _ensure_editable(self, transaction: Transaction) -> None:
        linked_payment = self.db.scalar(
            select(Bill.id).where(Bill.paid_transaction_id == transaction.id).limit(1)
        ) or self.db.scalar(
            select(LoanPayment.id).where(LoanPayment.transaction_id == transaction.id).limit(1)
        )
        if linked_payment or self._is_credit_card_account(transaction.account_id):
            raise HTTPException(
                status_code=409,
                detail="This transaction is part of a bill, loan, or credit-card operation and must be changed there.",
            )
        if transaction.destination_account_id and self._is_credit_card_account(
            transaction.destination_account_id
        ):
            raise HTTPException(
                status_code=409,
                detail="This transaction is part of a credit-card operation and must be changed there.",
            )

    def get_transaction(self, transaction_id: UUID) -> Transaction:
        transaction = self.db.scalar(
            select(Transaction).where(
                Transaction.id == transaction_id, Transaction.user_id == self.user_id
            )
        )
        if transaction is None:
            raise HTTPException(status_code=404, detail="Transaction not found.")
        return transaction

    def get_transactions(
        self,
        *,
        limit: int = 50,
        offset: int = 0,
        date_from: date | None = None,
        date_to: date | None = None,
        category: str | None = None,
        account_id: UUID | None = None,
        transaction_type: Literal["income", "expense", "transfer"] | None = None,
        min_amount: Decimal | None = None,
        max_amount: Decimal | None = None,
        sort: Literal["asc", "desc"] = "desc",
    ) -> list[Transaction]:
        query = select(Transaction).where(Transaction.user_id == self.user_id)
        if date_from:
            query = query.where(Transaction.transaction_date >= date_from)
        if date_to:
            query = query.where(Transaction.transaction_date <= date_to)
        if category:
            query = query.where(Transaction.category == category)
        if account_id:
            query = query.where(
                (Transaction.account_id == account_id)
                | (Transaction.destination_account_id == account_id)
            )
        if transaction_type:
            query = query.where(Transaction.transaction_type == transaction_type)
        if min_amount is not None:
            query = query.where(Transaction.amount >= min_amount)
        if max_amount is not None:
            query = query.where(Transaction.amount <= max_amount)
        order = Transaction.transaction_date.asc() if sort == "asc" else Transaction.transaction_date.desc()
        return list(self.db.scalars(query.order_by(order, Transaction.created_at.desc()).limit(limit).offset(offset)).all())

    def update_transaction(self, transaction_id: UUID, data: TransactionCreate) -> Transaction:
        transaction = self.get_transaction(transaction_id)
        self._ensure_editable(transaction)
        self._validate_accounts(data)
        try:
            self._apply_balance(transaction, -1)
            self._copy_fields(transaction, data)
            self._apply_balance(transaction, 1)
            self.db.commit()
        except Exception:
            self.db.rollback()
            raise
        self.db.refresh(transaction)
        return transaction

    def delete_transaction(self, transaction_id: UUID) -> None:
        transaction = self.get_transaction(transaction_id)
        self._ensure_editable(transaction)
        try:
            self._apply_balance(transaction, -1)
            self.db.delete(transaction)
            self.db.commit()
        except Exception:
            self.db.rollback()
            raise
