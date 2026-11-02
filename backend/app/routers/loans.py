"""Loan management, EMI schedules, and payment endpoints."""

from uuid import UUID

from fastapi import APIRouter, Depends, Query, Response, status
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user
from app.database.database import get_db
from app.models.user import User
from app.schemas.loan import (
    EmiScheduleItem,
    LoanCreate,
    LoanPaymentCreate,
    LoanPaymentRead,
    LoanRead,
    LoanUpdate,
)
from app.services.loan_service import LoanService

router = APIRouter(prefix="/api/loans", tags=["Loans"])


@router.get("", response_model=list[LoanRead])
def list_loans(
    limit: int = Query(default=100, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[LoanRead]:
    return LoanService(db, user.id).get_loans(limit=limit, offset=offset)


@router.post("", response_model=LoanRead, status_code=status.HTTP_201_CREATED)
def create_loan(
    data: LoanCreate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> LoanRead:
    return LoanService(db, user.id).create_loan(data)


@router.get("/{loan_id}/schedule", response_model=list[EmiScheduleItem])
def loan_schedule(
    loan_id: UUID,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[EmiScheduleItem]:
    return LoanService(db, user.id).generate_emi_schedule(loan_id)


@router.get("/{loan_id}/payments", response_model=list[LoanPaymentRead])
def loan_payments(
    loan_id: UUID,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[LoanPaymentRead]:
    return LoanService(db, user.id).get_payments(loan_id)


@router.post("/{loan_id}/payments", response_model=LoanPaymentRead, status_code=status.HTTP_201_CREATED)
def pay_loan_emi(
    loan_id: UUID,
    data: LoanPaymentCreate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> LoanPaymentRead:
    return LoanService(db, user.id).record_emi_payment(loan_id, data)


@router.get("/{loan_id}", response_model=LoanRead)
def get_loan(
    loan_id: UUID, user: User = Depends(get_current_user), db: Session = Depends(get_db)
) -> LoanRead:
    return LoanService(db, user.id).get_owned(loan_id)


@router.put("/{loan_id}", response_model=LoanRead)
def update_loan(
    loan_id: UUID,
    data: LoanUpdate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> LoanRead:
    return LoanService(db, user.id).update_loan(loan_id, data)


@router.delete("/{loan_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_loan(
    loan_id: UUID,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Response:
    LoanService(db, user.id).delete_loan(loan_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
