from app.schemas.base import APIModel
"""Transaction request and response validation."""

from datetime import date, datetime
from decimal import Decimal
from typing import Literal
from uuid import UUID

from pydantic import ConfigDict, Field, model_validator

TransactionType = Literal["income", "expense", "transfer"]


class TransactionCreate(APIModel):
    account_id: UUID
    destination_account_id: UUID | None = None
    transaction_type: TransactionType
    amount: Decimal = Field(gt=0, max_digits=14, decimal_places=2)
    category: str = Field(min_length=1, max_length=80)
    description: str = Field(min_length=1, max_length=240)
    transaction_date: date
    merchant: str | None = Field(default=None, max_length=160)
    notes: str | None = Field(default=None, max_length=1000)

    @model_validator(mode="after")
    def validate_transfer_accounts(self) -> "TransactionCreate":
        if self.transaction_type == "transfer" and self.destination_account_id is None:
            raise ValueError("A transfer requires destination_account_id.")
        if self.transaction_type != "transfer" and self.destination_account_id is not None:
            raise ValueError("Only transfers may have destination_account_id.")
        if self.destination_account_id == self.account_id:
            raise ValueError("Source and destination accounts must be different.")
        return self


class TransactionRead(APIModel):
    id: UUID
    user_id: UUID
    account_id: UUID
    destination_account_id: UUID | None
    transaction_type: str
    amount: Decimal
    category: str
    description: str
    transaction_date: date
    merchant: str | None
    notes: str | None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
