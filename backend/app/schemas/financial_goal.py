from app.schemas.base import APIModel
"""Savings goal request and response validation."""

from datetime import date
from decimal import Decimal
from typing import Literal
from uuid import UUID

from pydantic import ConfigDict, Field


class FinancialGoalCreate(APIModel):
    goal_name: str = Field(min_length=1, max_length=160)
    target_amount: Decimal = Field(gt=0, max_digits=14, decimal_places=2)
    target_date: date | None = None


class FinancialGoalUpdate(APIModel):
    goal_name: str | None = Field(default=None, min_length=1, max_length=160)
    target_amount: Decimal | None = Field(default=None, gt=0, max_digits=14, decimal_places=2)
    target_date: date | None = None
    status: Literal["active", "completed", "cancelled"] | None = None


class GoalContribution(APIModel):
    amount: Decimal = Field(gt=0, max_digits=14, decimal_places=2)


class FinancialGoalRead(APIModel):
    id: UUID
    user_id: UUID
    goal_name: str
    target_amount: Decimal
    current_amount: Decimal
    target_date: date | None
    status: str

    model_config = ConfigDict(from_attributes=True)


class GoalProgress(APIModel):
    goal: FinancialGoalRead
    remaining_amount: Decimal
    percent_complete: float
    required_monthly_savings: Decimal | None
