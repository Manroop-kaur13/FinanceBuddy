"""Personalized dashboard summary calculations."""

import calendar
from datetime import date
from decimal import Decimal
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.account import Account
from app.models.credit_card import CreditCard
from app.models.investment import Investment
from app.models.loan import Loan
from app.models.transaction import Transaction
from app.schemas.analytics import DashboardSummary
from app.services.analytics_service import AnalyticsService
from app.services.bill_service import BillService
from app.services.budget_service import BudgetService
from app.services.financial_goal_service import FinancialGoalService


class DashboardService:
    """Assemble account, ledger, budget, bill, goal, loan, and investment data."""

    def __init__(self, db: Session, user_id: UUID) -> None:
        self.db = db
        self.user_id = user_id

    def _sum(self, model: type, column, *, exclude_credit_card: bool = False) -> Decimal:
        query = select(func.coalesce(func.sum(column), 0)).where(model.user_id == self.user_id)
        if exclude_credit_card:
            query = query.where(Account.account_type != "credit_card")
        return Decimal(self.db.scalar(query) or 0)

    def get_summary(self, *, today: date | None = None) -> DashboardSummary:
        current = today or date.today()
        start = date(current.year, current.month, 1)
        total_balance = self._sum(Account, Account.current_balance, exclude_credit_card=True)
        income, expenses = AnalyticsService(self.db, self.user_id).period_totals(
            start=start, end=current
        )
        investment_value = self._sum(
            Investment,
            Investment.quantity * Investment.current_price,
        )
        loan_outstanding = self._sum(Loan, Loan.outstanding_balance)
        credit_outstanding = self._sum(CreditCard, CreditCard.outstanding_amount)
        recent = list(
            self.db.scalars(
                select(Transaction)
                .where(Transaction.user_id == self.user_id)
                .order_by(Transaction.transaction_date.desc(), Transaction.created_at.desc())
                .limit(10)
            ).all()
        )
        analytics = AnalyticsService(self.db, self.user_id)
        budget_service = BudgetService(self.db, self.user_id)
        budgets = budget_service.get_budgets(limit=100)
        budget_progress = [
            budget_service.get_budget_progress(item.id, today=current)
            for item in budgets
        ]
        goal_service = FinancialGoalService(self.db, self.user_id)
        goals = goal_service.get_goals(limit=100)
        goal_progress = [
            goal_service.get_goal_progress(item.id, today=current)
            for item in goals
        ]
        return DashboardSummary(
            as_of=current,
            total_balance=total_balance,
            total_income=income,
            total_expenses=expenses,
            savings=income - expenses,
            net_worth=total_balance + investment_value - loan_outstanding - credit_outstanding,
            investment_value=investment_value,
            loan_outstanding=loan_outstanding,
            credit_card_outstanding=credit_outstanding,
            recent_transactions=recent,
            cash_flow=analytics.monthly_cash_flow(today=current),
            category_spending=analytics.spending_by_category(date_from=start, date_to=current),
            budget_progress=budget_progress,
            upcoming_bills=BillService(self.db, self.user_id).get_upcoming_bills(
                through=date(
                    current.year,
                    current.month,
                    calendar.monthrange(current.year, current.month)[1],
                )
            ),
            goal_progress=goal_progress,
        )
