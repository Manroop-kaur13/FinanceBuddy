"""Bill management and payment endpoints."""

from datetime import date
from uuid import UUID

from fastapi import APIRouter, Depends, Query, Response, status
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user
from app.database.database import get_db
from app.models.user import User
from app.schemas.bill import BillCreate, BillPaymentRequest, BillRead, BillUpdate
from app.services.bill_service import BillService

router = APIRouter(prefix="/api/bills", tags=["Bills"])


@router.get("/upcoming", response_model=list[BillRead])
def upcoming_bills(
    through: date = Query(...),
    limit: int = Query(default=100, ge=1, le=100),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[BillRead]:
    return BillService(db, user.id).get_upcoming_bills(through=through, limit=limit)


@router.get("/overdue", response_model=list[BillRead])
def overdue_bills(
    user: User = Depends(get_current_user), db: Session = Depends(get_db)
) -> list[BillRead]:
    return BillService(db, user.id).get_overdue_bills()


@router.get("", response_model=list[BillRead])
def list_bills(
    limit: int = Query(default=100, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[BillRead]:
    return BillService(db, user.id).get_bills(limit=limit, offset=offset)


@router.post("", response_model=BillRead, status_code=status.HTTP_201_CREATED)
def create_bill(
    data: BillCreate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> BillRead:
    return BillService(db, user.id).create_bill(data)


@router.post("/{bill_id}/pay", response_model=BillRead)
def pay_bill(
    bill_id: UUID,
    data: BillPaymentRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> BillRead:
    return BillService(db, user.id).mark_bill_paid(bill_id, account_id=data.account_id)


@router.get("/{bill_id}", response_model=BillRead)
def get_bill(
    bill_id: UUID, user: User = Depends(get_current_user), db: Session = Depends(get_db)
) -> BillRead:
    return BillService(db, user.id).get_owned(bill_id)


@router.put("/{bill_id}", response_model=BillRead)
def update_bill(
    bill_id: UUID,
    data: BillUpdate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> BillRead:
    return BillService(db, user.id).update_bill(bill_id, data)


@router.delete("/{bill_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_bill(
    bill_id: UUID,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Response:
    BillService(db, user.id).delete_bill(bill_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
