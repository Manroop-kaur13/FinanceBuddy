from app.schemas.base import APIModel
"""Budget request and response validation."""

from datetime import date
from decimal import Decimal
from typing import Literal
from uuid import UUID

from pydantic import ConfigDict, Field


class BudgetCreate(APIModel):
    category: str = Field(min_length=1, max_length=80)
    budget_limit: Decimal = Field(gt=0, max_digits=14, decimal_places=2)
    period: Literal["weekly", "monthly", "yearly"] = "monthly"
    start_date: date


class BudgetUpdate(APIModel):
    category: str | None = Field(default=None, min_length=1, max_length=80)
    budget_limit: Decimal | None = Field(default=None, gt=0, max_digits=14, decimal_places=2)
    period: Literal["weekly", "monthly", "yearly"] | None = None
    start_date: date | None = None


class BudgetRead(APIModel):
    id: UUID
    user_id: UUID
    category: str
    budget_limit: Decimal
    period: str
    start_date: date

    model_config = ConfigDict(from_attributes=True)


class BudgetProgress(APIModel):
    budget: BudgetRead
    spent: Decimal
    remaining: Decimal
    percent_used: float
    status: str
    window_start: date
    window_end: date
