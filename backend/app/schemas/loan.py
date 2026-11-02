from app.schemas.base import APIModel
"""Loan and EMI request/response validation."""

from datetime import date
from decimal import Decimal
from uuid import UUID

from pydantic import ConfigDict, Field


class LoanCreate(APIModel):
    loan_name: str = Field(min_length=1, max_length=160)
    principal: Decimal = Field(gt=0, max_digits=14, decimal_places=2)
    interest_rate: Decimal = Field(ge=0, le=100, max_digits=7, decimal_places=4)
    tenure_months: int = Field(gt=0, le=600)
    start_date: date


class LoanUpdate(APIModel):
    loan_name: str | None = Field(default=None, min_length=1, max_length=160)
    interest_rate: Decimal | None = Field(default=None, ge=0, le=100, max_digits=7, decimal_places=4)
    tenure_months: int | None = Field(default=None, gt=0, le=600)


class LoanRead(APIModel):
    id: UUID
    user_id: UUID
    loan_name: str
    principal: Decimal
    interest_rate: Decimal
    tenure_months: int
    start_date: date
    emi_amount: Decimal
    outstanding_balance: Decimal
    status: str

    model_config = ConfigDict(from_attributes=True)


class LoanPaymentCreate(APIModel):
    account_id: UUID
    payment_date: date


class LoanPaymentRead(APIModel):
    id: UUID
    loan_id: UUID
    transaction_id: UUID
    amount: Decimal
    principal_paid: Decimal
    interest_paid: Decimal
    payment_date: date

    model_config = ConfigDict(from_attributes=True)


class EmiScheduleItem(APIModel):
    installment_number: int
    payment_date: date
    emi_amount: Decimal
    principal_paid: Decimal
    interest_paid: Decimal
    outstanding_balance: Decimal
