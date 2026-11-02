"""Credit card limits, purchases, payments, and statements."""

from datetime import date
from decimal import Decimal
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.account import Account
from app.models.credit_card import CreditCard
from app.models.transaction import Transaction
from app.schemas.credit_card import (
    CardExpenseCreate,
    CardPaymentCreate,
    CreditCardCreate,
    CreditCardRead,
    CreditCardUpdate,
)
from app.schemas.transaction import TransactionCreate
from app.services.base import OwnedService
from app.services.transaction_service import TransactionService


class CreditCardService(OwnedService):
    """Record card purchases as expenses and card repayments as transfers."""

    model = CreditCard

    def __init__(self, db: Session, user_id: UUID) -> None:
        super().__init__(db, user_id)

    def _account(self, account_id: UUID) -> Account:
        account = self.db.scalar(
            select(Account).where(Account.id == account_id, Account.user_id == self.user_id)
        )
        if account is None:
            raise HTTPException(status_code=404, detail="Account not found.")
        return account

    @staticmethod
    def _read(card: CreditCard) -> CreditCardRead:
        return CreditCardRead(
            id=card.id,
            user_id=card.user_id,
            account_id=card.account_id,
            card_name=card.card_name,
            credit_limit=card.credit_limit,
            outstanding_amount=card.outstanding_amount,
            available_credit=max(Decimal("0.00"), card.credit_limit - card.outstanding_amount),
            billing_cycle=card.billing_cycle,
            due_date=card.due_date,
        )

    def add_credit_card(self, data: CreditCardCreate) -> CreditCardRead:
        account = self._account(data.account_id)
        if account.account_type != "credit_card":
            raise HTTPException(status_code=422, detail="The linked account must be a credit-card account.")
        exists = self.db.scalar(
            select(CreditCard.id).where(CreditCard.account_id == account.id).limit(1)
        )
        if exists:
            raise HTTPException(status_code=409, detail="This account already has a credit card.")
        card = CreditCard(user_id=self.user_id, outstanding_amount=Decimal("0.00"), **data.model_dump())
        self.db.add(card)
        self.db.commit()
        self.db.refresh(card)
        return self._read(card)

    def get_credit_cards(self, *, limit: int = 100, offset: int = 0) -> list[CreditCardRead]:
        return [self._read(card) for card in self.list_owned(limit=limit, offset=offset)]

    def get_credit_card(self, card_id: UUID) -> CreditCard:
        return self.get_owned(card_id)

    def update_credit_card(self, card_id: UUID, data: CreditCardUpdate) -> CreditCardRead:
        card = self.get_owned(card_id)
        values = data.model_dump(exclude_unset=True)
        if values.get("credit_limit") is not None and values["credit_limit"] < card.outstanding_amount:
            raise HTTPException(status_code=422, detail="Credit limit cannot be below the outstanding amount.")
        for field, value in values.items():
            if value is not None:
                setattr(card, field, value)
        self.db.commit()
        self.db.refresh(card)
        return self._read(card)

    def delete_credit_card(self, card_id: UUID) -> None:
        card = self.get_owned(card_id)
        if card.outstanding_amount > 0:
            raise HTTPException(status_code=409, detail="Pay off the card before deleting it.")
        self.db.delete(card)
        self.db.commit()

    def calculate_available_credit(self, card_id: UUID) -> Decimal:
        card = self.get_owned(card_id)
        return max(Decimal("0.00"), card.credit_limit - card.outstanding_amount)

    def record_card_expense(self, card_id: UUID, data: CardExpenseCreate) -> Transaction:
        card = self.get_owned(card_id)
        if data.amount > self.calculate_available_credit(card_id):
            raise HTTPException(status_code=422, detail="Expense exceeds available credit.")
        transaction = TransactionService(self.db, self.user_id).add_transaction(
            TransactionCreate(
                account_id=card.account_id,
                transaction_type="expense",
                amount=data.amount,
                category=data.category,
                description=data.description,
                transaction_date=data.transaction_date,
                merchant=data.merchant,
                notes=data.notes,
            ),
            commit=False,
            internal_card_operation=True,
        )
        card.outstanding_amount += data.amount
        self.db.commit()
        self.db.refresh(transaction)
        return transaction

    def record_card_payment(self, card_id: UUID, data: CardPaymentCreate) -> Transaction:
        card = self.get_owned(card_id)
        if data.amount > card.outstanding_amount:
            raise HTTPException(status_code=422, detail="Payment exceeds the outstanding card balance.")
        source = self._account(data.source_account_id)
        destination = self._account(card.account_id)
        if source.currency != destination.currency:
            raise HTTPException(status_code=422, detail="Card payments require matching currencies.")
        transaction = TransactionService(self.db, self.user_id).add_transaction(
            TransactionCreate(
                account_id=source.id,
                destination_account_id=destination.id,
                transaction_type="transfer",
                amount=data.amount,
                category="Credit card payment",
                description=f"Payment to {card.card_name}",
                transaction_date=data.payment_date,
            ),
            commit=False,
            internal_card_operation=True,
        )
        card.outstanding_amount -= data.amount
        self.db.commit()
        self.db.refresh(transaction)
        return transaction

    def get_statement(
        self, card_id: UUID, *, date_from: date | None = None, date_to: date | None = None
    ) -> list[Transaction]:
        card = self.get_owned(card_id)
        query = select(Transaction).where(
            Transaction.user_id == self.user_id,
            (Transaction.account_id == card.account_id)
            | (Transaction.destination_account_id == card.account_id),
        )
        if date_from:
            query = query.where(Transaction.transaction_date >= date_from)
        if date_to:
            query = query.where(Transaction.transaction_date <= date_to)
        return list(self.db.scalars(query.order_by(Transaction.transaction_date.desc())).all())
