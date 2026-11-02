from app.schemas.base import APIModel
"""Investment holding request and response validation."""

from datetime import date
from decimal import Decimal
from uuid import UUID

from pydantic import ConfigDict, Field


class InvestmentCreate(APIModel):
    investment_name: str = Field(min_length=1, max_length=160)
    investment_type: str = Field(min_length=1, max_length=60)
    quantity: Decimal = Field(gt=0, max_digits=20, decimal_places=8)
    purchase_price: Decimal = Field(ge=0, max_digits=14, decimal_places=4)
    current_price: Decimal = Field(ge=0, max_digits=14, decimal_places=4)
    purchase_date: date


class InvestmentUpdate(APIModel):
    investment_name: str | None = Field(default=None, min_length=1, max_length=160)
    investment_type: str | None = Field(default=None, min_length=1, max_length=60)
    quantity: Decimal | None = Field(default=None, gt=0, max_digits=20, decimal_places=8)
    purchase_price: Decimal | None = Field(default=None, ge=0, max_digits=14, decimal_places=4)
    current_price: Decimal | None = Field(default=None, ge=0, max_digits=14, decimal_places=4)
    purchase_date: date | None = None


class InvestmentRead(APIModel):
    id: UUID
    user_id: UUID
    investment_name: str
    investment_type: str
    quantity: Decimal
    purchase_price: Decimal
    current_price: Decimal
    purchase_date: date

    model_config = ConfigDict(from_attributes=True)


class InvestmentValue(APIModel):
    investment: InvestmentRead
    current_value: Decimal
    gain_loss: Decimal


class PortfolioSummary(APIModel):
    total_value: Decimal
    total_cost: Decimal
    total_gain_loss: Decimal
    holdings: list[InvestmentValue]
