"""Budget CRUD and spending progress endpoints."""

from uuid import UUID

from fastapi import APIRouter, Depends, Query, Response, status
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user
from app.database.database import get_db
from app.models.user import User
from app.schemas.budget import BudgetCreate, BudgetProgress, BudgetRead, BudgetUpdate
from app.services.budget_service import BudgetService

router = APIRouter(prefix="/api/budgets", tags=["Budgets"])


@router.get("", response_model=list[BudgetRead])
def list_budgets(
    limit: int = Query(default=100, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[BudgetRead]:
    return BudgetService(db, user.id).get_budgets(limit=limit, offset=offset)


@router.post("", response_model=BudgetRead, status_code=status.HTTP_201_CREATED)
def create_budget(
    data: BudgetCreate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> BudgetRead:
    return BudgetService(db, user.id).create_budget(data)


@router.get("/{budget_id}/progress", response_model=BudgetProgress)
def budget_progress(
    budget_id: UUID,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> BudgetProgress:
    return BudgetService(db, user.id).get_budget_progress(budget_id)


@router.get("/{budget_id}", response_model=BudgetRead)
def get_budget(
    budget_id: UUID, user: User = Depends(get_current_user), db: Session = Depends(get_db)
) -> BudgetRead:
    return BudgetService(db, user.id).get_owned(budget_id)


@router.put("/{budget_id}", response_model=BudgetRead)
def update_budget(
    budget_id: UUID,
    data: BudgetUpdate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> BudgetRead:
    return BudgetService(db, user.id).update_budget(budget_id, data)


@router.delete("/{budget_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_budget(
    budget_id: UUID,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Response:
    BudgetService(db, user.id).delete_budget(budget_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
