from app.schemas.base import APIModel
"""Credit card request and response validation."""

from datetime import date
from decimal import Decimal
from uuid import UUID

from pydantic import ConfigDict, Field


class CreditCardCreate(APIModel):
    account_id: UUID
    card_name: str = Field(min_length=1, max_length=120)
    credit_limit: Decimal = Field(gt=0, max_digits=14, decimal_places=2)
    billing_cycle: int = Field(ge=1, le=31)
    due_date: date | None = None


class CreditCardUpdate(APIModel):
    card_name: str | None = Field(default=None, min_length=1, max_length=120)
    credit_limit: Decimal | None = Field(default=None, gt=0, max_digits=14, decimal_places=2)
    billing_cycle: int | None = Field(default=None, ge=1, le=31)
    due_date: date | None = None


class CardExpenseCreate(APIModel):
    amount: Decimal = Field(gt=0, max_digits=14, decimal_places=2)
    category: str = Field(min_length=1, max_length=80)
    description: str = Field(min_length=1, max_length=240)
    transaction_date: date
    merchant: str | None = Field(default=None, max_length=160)
    notes: str | None = Field(default=None, max_length=1000)


class CardPaymentCreate(APIModel):
    source_account_id: UUID
    amount: Decimal = Field(gt=0, max_digits=14, decimal_places=2)
    payment_date: date


class CreditCardRead(APIModel):
    id: UUID
    user_id: UUID
    account_id: UUID
    card_name: str
    credit_limit: Decimal
    outstanding_amount: Decimal
    available_credit: Decimal
    billing_cycle: int
    due_date: date | None

    model_config = ConfigDict(from_attributes=True)
