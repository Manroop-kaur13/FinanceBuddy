from app.schemas.base import APIModel
"""Dashboard and analytics response schemas."""

from datetime import date
from decimal import Decimal

from app.schemas.bill import BillRead
from app.schemas.budget import BudgetProgress
from app.schemas.financial_goal import GoalProgress
from app.schemas.transaction import TransactionRead


class CashFlowMonth(APIModel):
    month: str
    income: Decimal
    expenses: Decimal
    savings: Decimal


class CategorySpending(APIModel):
    category: str
    amount: Decimal


class DashboardSummary(APIModel):
    as_of: date
    total_balance: Decimal
    total_income: Decimal
    total_expenses: Decimal
    savings: Decimal
    net_worth: Decimal
    investment_value: Decimal
    loan_outstanding: Decimal
    credit_card_outstanding: Decimal
    recent_transactions: list[TransactionRead]
    cash_flow: list[CashFlowMonth]
    category_spending: list[CategorySpending]
    budget_progress: list[BudgetProgress]
    upcoming_bills: list[BillRead]
    goal_progress: list[GoalProgress]
