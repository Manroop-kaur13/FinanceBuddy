from app.schemas.base import APIModel
"""Account request and response validation."""

from datetime import datetime
from decimal import Decimal
from typing import Literal
from uuid import UUID

from pydantic import ConfigDict, Field

AccountType = Literal["bank", "cash", "debit_card", "credit_card", "digital_wallet", "savings"]


class AccountCreate(APIModel):
    account_name: str = Field(min_length=1, max_length=120)
    account_type: AccountType
    currency: str = Field(default="INR", min_length=3, max_length=3, pattern="^[A-Z]{3}$")
    opening_balance: Decimal = Field(ge=0, max_digits=14, decimal_places=2)


class AccountUpdate(APIModel):
    account_name: str | None = Field(default=None, min_length=1, max_length=120)
    currency: str | None = Field(default=None, min_length=3, max_length=3, pattern="^[A-Z]{3}$")


class AccountRead(APIModel):
    id: UUID
    user_id: UUID
    account_name: str
    account_type: str
    currency: str
    opening_balance: Decimal
    current_balance: Decimal
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
