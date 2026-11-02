"""Savings goal CRUD and contribution operations."""

from datetime import date
from decimal import Decimal, ROUND_UP
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.financial_goal import FinancialGoal
from app.schemas.financial_goal import (
    FinancialGoalCreate,
    FinancialGoalUpdate,
    GoalContribution,
    GoalProgress,
    FinancialGoalRead,
)
from app.services.base import OwnedService


class FinancialGoalService(OwnedService):
    """Track goal balances, completion, and required monthly contribution."""

    model = FinancialGoal

    def __init__(self, db: Session, user_id: UUID) -> None:
        super().__init__(db, user_id)

    def create_goal(self, data: FinancialGoalCreate) -> FinancialGoal:
        goal = FinancialGoal(
            user_id=self.user_id,
            **data.model_dump(),
            current_amount=Decimal("0.00"),
            status="active",
        )
        self.db.add(goal)
        self.db.commit()
        self.db.refresh(goal)
        return goal

    def get_goals(self, *, limit: int = 100, offset: int = 0) -> list[FinancialGoal]:
        return self.list_owned(limit=limit, offset=offset)

    def update_goal(self, goal_id: UUID, data: FinancialGoalUpdate) -> FinancialGoal:
        goal = self.get_owned(goal_id)
        self.apply_updates(goal, data)
        if goal.current_amount >= goal.target_amount:
            goal.status = "completed"
        self.db.commit()
        self.db.refresh(goal)
        return goal

    def delete_goal(self, goal_id: UUID) -> None:
        self.db.delete(self.get_owned(goal_id))
        self.db.commit()

    def add_contribution(self, goal_id: UUID, contribution: GoalContribution) -> FinancialGoal:
        goal = self.get_owned(goal_id)
        if goal.status != "active":
            raise HTTPException(status_code=409, detail="Only active goals accept contributions.")
        goal.current_amount = min(goal.target_amount, goal.current_amount + contribution.amount)
        if goal.current_amount >= goal.target_amount:
            goal.status = "completed"
        self.db.commit()
        self.db.refresh(goal)
        return goal

    def get_goal_progress(self, goal_id: UUID, *, today: date | None = None) -> GoalProgress:
        goal = self.get_owned(goal_id)
        current_date = today or date.today()
        remaining = max(Decimal("0.00"), goal.target_amount - goal.current_amount)
        percent = min(100.0, float(goal.current_amount / goal.target_amount * 100))
        monthly = None
        if goal.target_date and remaining > 0 and goal.target_date >= current_date:
            month_count = max(
                1,
                (goal.target_date.year - current_date.year) * 12
                + goal.target_date.month
                - current_date.month,
            )
            monthly = (remaining / month_count).quantize(Decimal("0.01"), rounding=ROUND_UP)
        return GoalProgress(
            goal=FinancialGoalRead.model_validate(goal),
            remaining_amount=remaining,
            percent_complete=percent,
            required_monthly_savings=monthly,
        )

    def check_goal_completion(self, goal_id: UUID) -> bool:
        goal = self.get_owned(goal_id)
        return goal.current_amount >= goal.target_amount
