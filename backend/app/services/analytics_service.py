"""Database-backed cash-flow and category analytics."""

import calendar
from datetime import date
from decimal import Decimal
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.transaction import Transaction
from app.schemas.analytics import CashFlowMonth, CategorySpending


class AnalyticsService:
    """Aggregate only the signed-in user's actual ledger transactions."""

    def __init__(self, db: Session, user_id: UUID) -> None:
        self.db = db
        self.user_id = user_id

    def _month_sum(self, kind: str, start: date, end: date) -> Decimal:
        amount = self.db.scalar(
            select(func.coalesce(func.sum(Transaction.amount), 0)).where(
                Transaction.user_id == self.user_id,
                Transaction.transaction_type == kind,
                Transaction.transaction_date >= start,
                Transaction.transaction_date <= end,
            )
        )
        return Decimal(amount or 0)

    def monthly_cash_flow(self, *, today: date | None = None, months: int = 6) -> list[CashFlowMonth]:
        current = today or date.today()
        month_index = current.year * 12 + current.month - 1
        results: list[CashFlowMonth] = []
        for offset in reversed(range(months)):
            index = month_index - offset
            year, month_zero = divmod(index, 12)
            month = month_zero + 1
            start = date(year, month, 1)
            end = min(
                date(year, month, calendar.monthrange(year, month)[1]),
                current,
            )
            income = self._month_sum("income", start, end)
            expenses = self._month_sum("expense", start, end)
            results.append(
                CashFlowMonth(
                    month=f"{year:04d}-{month:02d}",
                    income=income,
                    expenses=expenses,
                    savings=income - expenses,
                )
            )
        return results

    def spending_by_category(
        self, *, date_from: date | None = None, date_to: date | None = None
    ) -> list[CategorySpending]:
        query = (
            select(Transaction.category, func.sum(Transaction.amount).label("amount"))
            .where(
                Transaction.user_id == self.user_id,
                Transaction.transaction_type == "expense",
            )
            .group_by(Transaction.category)
        )
        if date_from:
            query = query.where(Transaction.transaction_date >= date_from)
        if date_to:
            query = query.where(Transaction.transaction_date <= date_to)
        rows = self.db.execute(query.order_by(func.sum(Transaction.amount).desc())).all()
        return [CategorySpending(category=row.category, amount=row.amount) for row in rows]

    def period_totals(self, *, start: date, end: date) -> tuple[Decimal, Decimal]:
        return self._month_sum("income", start, end), self._month_sum("expense", start, end)
