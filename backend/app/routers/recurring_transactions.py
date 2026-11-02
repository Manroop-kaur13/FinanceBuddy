"""Recurring transaction schedule endpoints."""

from uuid import UUID

from fastapi import APIRouter, Depends, Query, Response, status
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user
from app.database.database import get_db
from app.models.user import User
from app.schemas.recurring_transaction import (
    RecurringTransactionCreate,
    RecurringTransactionRead,
    RecurringTransactionUpdate,
)
from app.services.recurring_transaction_service import RecurringTransactionService

router = APIRouter(prefix="/api/recurring-transactions", tags=["Recurring transactions"])


@router.get("", response_model=list[RecurringTransactionRead])
def list_schedules(
    limit: int = Query(default=100, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[RecurringTransactionRead]:
    return RecurringTransactionService(db, user.id).get_schedules(limit=limit, offset=offset)


@router.post("", response_model=RecurringTransactionRead, status_code=status.HTTP_201_CREATED)
def create_schedule(
    data: RecurringTransactionCreate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> RecurringTransactionRead:
    return RecurringTransactionService(db, user.id).create_schedule(data)


@router.get("/{schedule_id}", response_model=RecurringTransactionRead)
def get_schedule(
    schedule_id: UUID, user: User = Depends(get_current_user), db: Session = Depends(get_db)
) -> RecurringTransactionRead:
    return RecurringTransactionService(db, user.id).get_owned(schedule_id)


@router.put("/{schedule_id}", response_model=RecurringTransactionRead)
def update_schedule(
    schedule_id: UUID,
    data: RecurringTransactionUpdate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> RecurringTransactionRead:
    return RecurringTransactionService(db, user.id).update_schedule(schedule_id, data)


@router.delete("/{schedule_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_schedule(
    schedule_id: UUID,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Response:
    RecurringTransactionService(db, user.id).delete_schedule(schedule_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
