"""Financial goal management and contribution endpoints."""

from uuid import UUID

from fastapi import APIRouter, Depends, Query, Response, status
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user
from app.database.database import get_db
from app.models.user import User
from app.schemas.financial_goal import (
    FinancialGoalCreate,
    FinancialGoalRead,
    FinancialGoalUpdate,
    GoalContribution,
    GoalProgress,
)
from app.services.financial_goal_service import FinancialGoalService

router = APIRouter(prefix="/api/goals", tags=["Financial goals"])


@router.get("", response_model=list[FinancialGoalRead])
def list_goals(
    limit: int = Query(default=100, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[FinancialGoalRead]:
    return FinancialGoalService(db, user.id).get_goals(limit=limit, offset=offset)


@router.post("", response_model=FinancialGoalRead, status_code=status.HTTP_201_CREATED)
def create_goal(
    data: FinancialGoalCreate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> FinancialGoalRead:
    return FinancialGoalService(db, user.id).create_goal(data)


@router.post("/{goal_id}/contributions", response_model=FinancialGoalRead)
def contribute_to_goal(
    goal_id: UUID,
    data: GoalContribution,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> FinancialGoalRead:
    return FinancialGoalService(db, user.id).add_contribution(goal_id, data)


@router.get("/{goal_id}/progress", response_model=GoalProgress)
def goal_progress(
    goal_id: UUID,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> GoalProgress:
    return FinancialGoalService(db, user.id).get_goal_progress(goal_id)


@router.get("/{goal_id}", response_model=FinancialGoalRead)
def get_goal(
    goal_id: UUID, user: User = Depends(get_current_user), db: Session = Depends(get_db)
) -> FinancialGoalRead:
    return FinancialGoalService(db, user.id).get_owned(goal_id)


@router.put("/{goal_id}", response_model=FinancialGoalRead)
def update_goal(
    goal_id: UUID,
    data: FinancialGoalUpdate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> FinancialGoalRead:
    return FinancialGoalService(db, user.id).update_goal(goal_id, data)


@router.delete("/{goal_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_goal(
    goal_id: UUID,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Response:
    FinancialGoalService(db, user.id).delete_goal(goal_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
