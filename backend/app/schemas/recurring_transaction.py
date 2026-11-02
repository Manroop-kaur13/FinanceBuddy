from app.schemas.base import APIModel
"""Recurring transaction request and response validation."""

from datetime import date, datetime
from decimal import Decimal
from typing import Literal
from uuid import UUID

from pydantic import ConfigDict, Field


class RecurringTransactionCreate(APIModel):
    account_id: UUID
    transaction_type: Literal["income", "expense"]
    amount: Decimal = Field(gt=0, max_digits=14, decimal_places=2)
    category: str = Field(min_length=1, max_length=80)
    description: str = Field(min_length=1, max_length=240)
    frequency: Literal["weekly", "monthly", "yearly"]
    next_run_date: date


class RecurringTransactionUpdate(APIModel):
    account_id: UUID | None = None
    transaction_type: Literal["income", "expense"] | None = None
    amount: Decimal | None = Field(default=None, gt=0, max_digits=14, decimal_places=2)
    category: str | None = Field(default=None, min_length=1, max_length=80)
    description: str | None = Field(default=None, min_length=1, max_length=240)
    frequency: Literal["weekly", "monthly", "yearly"] | None = None
    next_run_date: date | None = None
    is_active: bool | None = None


class RecurringTransactionRead(APIModel):
    id: UUID
    user_id: UUID
    account_id: UUID
    transaction_type: str
    amount: Decimal
    category: str
    description: str
    frequency: str
    next_run_date: date
    is_active: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
