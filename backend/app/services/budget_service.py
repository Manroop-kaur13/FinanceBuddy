"""Budget CRUD and expense-based progress calculations."""

import calendar
from datetime import date, timedelta
from decimal import Decimal
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.budget import Budget
from app.models.transaction import Transaction
from app.schemas.budget import BudgetCreate, BudgetProgress, BudgetRead, BudgetUpdate
from app.services.base import OwnedService


class BudgetService(OwnedService):
    """Calculate budget progress from expense transactions only."""

    model = Budget

    def __init__(self, db: Session, user_id: UUID) -> None:
        super().__init__(db, user_id)

    def create_budget(self, data: BudgetCreate) -> Budget:
        budget = Budget(user_id=self.user_id, **data.model_dump())
        self.db.add(budget)
        self.db.commit()
        self.db.refresh(budget)
        return budget

    def get_budgets(self, *, limit: int = 100, offset: int = 0) -> list[Budget]:
        return self.list_owned(limit=limit, offset=offset)

    def update_budget(self, budget_id: UUID, data: BudgetUpdate) -> Budget:
        budget = self.get_owned(budget_id)
        self.apply_updates(budget, data)
        self.db.commit()
        self.db.refresh(budget)
        return budget

    def delete_budget(self, budget_id: UUID) -> None:
        self.db.delete(self.get_owned(budget_id))
        self.db.commit()

    @staticmethod
    def period_window(period: str, today: date) -> tuple[date, date]:
        if period == "weekly":
            start = today - timedelta(days=today.weekday())
            return start, start + timedelta(days=6)
        if period == "yearly":
            return date(today.year, 1, 1), date(today.year, 12, 31)
        start = date(today.year, today.month, 1)
        end = date(today.year, today.month, calendar.monthrange(today.year, today.month)[1])
        return start, end

    def calculate_spending(self, budget: Budget, *, today: date | None = None) -> Decimal:
        current_date = today or date.today()
        start, end = self.period_window(budget.period, current_date)
        if budget.start_date > current_date:
            return Decimal("0.00")
        start = max(start, budget.start_date)
        amount = self.db.scalar(
            select(func.coalesce(func.sum(Transaction.amount), 0)).where(
                Transaction.user_id == self.user_id,
                Transaction.transaction_type == "expense",
                Transaction.category == budget.category,
                Transaction.transaction_date >= start,
                Transaction.transaction_date <= end,
            )
        )
        return Decimal(amount or 0)

    def get_budget_progress(self, budget_id: UUID, *, today: date | None = None) -> BudgetProgress:
        budget = self.get_owned(budget_id)
        current_date = today or date.today()
        start, end = self.period_window(budget.period, current_date)
        start = max(start, budget.start_date)
        spent = self.calculate_spending(budget, today=current_date)
        remaining = budget.budget_limit - spent
        percent = float(spent / budget.budget_limit * 100)
        state = "over_budget" if spent > budget.budget_limit else "on_track"
        return BudgetProgress(
            budget=BudgetRead.model_validate(budget),
            spent=spent,
            remaining=remaining,
            percent_used=percent,
            status=state,
            window_start=start,
            window_end=end,
        )

    def check_budget_status(self, budget_id: UUID) -> str:
        return self.get_budget_progress(budget_id).status
