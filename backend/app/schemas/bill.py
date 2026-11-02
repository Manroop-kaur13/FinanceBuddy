from app.schemas.base import APIModel
"""Bill request and response validation."""

from datetime import date, datetime
from decimal import Decimal
from typing import Literal
from uuid import UUID

from pydantic import ConfigDict, Field


class BillCreate(APIModel):
    bill_name: str = Field(min_length=1, max_length=160)
    category: str = Field(min_length=1, max_length=80)
    amount: Decimal = Field(gt=0, max_digits=14, decimal_places=2)
    due_date: date
    account_id: UUID | None = None
    recurrence: Literal["weekly", "monthly", "quarterly", "yearly"] | None = None


class BillUpdate(APIModel):
    bill_name: str | None = Field(default=None, min_length=1, max_length=160)
    category: str | None = Field(default=None, min_length=1, max_length=80)
    amount: Decimal | None = Field(default=None, gt=0, max_digits=14, decimal_places=2)
    due_date: date | None = None
    account_id: UUID | None = None
    recurrence: Literal["weekly", "monthly", "quarterly", "yearly"] | None = None


class BillRead(APIModel):
    id: UUID
    user_id: UUID
    bill_name: str
    category: str
    amount: Decimal
    due_date: date
    account_id: UUID | None
    paid_transaction_id: UUID | None
    status: str
    recurrence: str | None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class BillPaymentRequest(APIModel):
    account_id: UUID | None = None
