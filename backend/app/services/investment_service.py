"""Investment CRUD and portfolio valuation."""

from decimal import Decimal
from uuid import UUID

from sqlalchemy.orm import Session

from app.models.investment import Investment
from app.schemas.investment import (
    InvestmentCreate,
    InvestmentRead,
    InvestmentUpdate,
    InvestmentValue,
    PortfolioSummary,
)
from app.services.base import OwnedService


class InvestmentService(OwnedService):
    """Calculate portfolio value and gain/loss from saved prices and quantities."""

    model = Investment

    def __init__(self, db: Session, user_id: UUID) -> None:
        super().__init__(db, user_id)

    @staticmethod
    def calculate_current_value(investment: Investment) -> Decimal:
        return (investment.quantity * investment.current_price).quantize(Decimal("0.01"))

    @staticmethod
    def calculate_gain_loss(investment: Investment) -> Decimal:
        return (investment.quantity * (investment.current_price - investment.purchase_price)).quantize(Decimal("0.01"))

    @classmethod
    def _value(cls, investment: Investment) -> InvestmentValue:
        return InvestmentValue(
            investment=InvestmentRead.model_validate(investment),
            current_value=cls.calculate_current_value(investment),
            gain_loss=cls.calculate_gain_loss(investment),
        )

    def add_investment(self, data: InvestmentCreate) -> Investment:
        investment = Investment(user_id=self.user_id, **data.model_dump())
        self.db.add(investment)
        self.db.commit()
        self.db.refresh(investment)
        return investment

    def get_investments(self, *, limit: int = 100, offset: int = 0) -> list[Investment]:
        return self.list_owned(limit=limit, offset=offset)

    def update_investment(self, investment_id: UUID, data: InvestmentUpdate) -> Investment:
        investment = self.get_owned(investment_id)
        self.apply_updates(investment, data)
        self.db.commit()
        self.db.refresh(investment)
        return investment

    def delete_investment(self, investment_id: UUID) -> None:
        self.db.delete(self.get_owned(investment_id))
        self.db.commit()

    def get_portfolio_summary(self) -> PortfolioSummary:
        values = [self._value(item) for item in self.get_investments()]
        total_value = sum((item.current_value for item in values), Decimal("0.00"))
        total_cost = sum(
            (item.investment.quantity * item.investment.purchase_price for item in values),
            Decimal("0.00"),
        )
        return PortfolioSummary(
            total_value=total_value,
            total_cost=total_cost,
            total_gain_loss=total_value - total_cost,
            holdings=values,
        )
