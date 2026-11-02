"""Transaction creation, history, filtering, and correction endpoints."""

from datetime import date
from decimal import Decimal
from typing import Literal
from uuid import UUID

from fastapi import APIRouter, Depends, Query, Response, status
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user
from app.database.database import get_db
from app.models.user import User
from app.schemas.transaction import TransactionCreate, TransactionRead
from app.services.transaction_service import TransactionService

router = APIRouter(prefix="/api/transactions", tags=["Transactions"])


@router.get("", response_model=list[TransactionRead])
def list_transactions(
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    date_from: date | None = None,
    date_to: date | None = None,
    category: str | None = None,
    account_id: UUID | None = None,
    transaction_type: Literal["income", "expense", "transfer"] | None = None,
    min_amount: Decimal | None = Query(default=None, ge=0),
    max_amount: Decimal | None = Query(default=None, ge=0),
    sort: Literal["asc", "desc"] = "desc",
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[TransactionRead]:
    return TransactionService(db, user.id).get_transactions(
        limit=limit,
        offset=offset,
        date_from=date_from,
        date_to=date_to,
        category=category,
        account_id=account_id,
        transaction_type=transaction_type,
        min_amount=min_amount,
        max_amount=max_amount,
        sort=sort,
    )


@router.post("", response_model=TransactionRead, status_code=status.HTTP_201_CREATED)
def create_transaction(
    data: TransactionCreate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> TransactionRead:
    return TransactionService(db, user.id).add_transaction(data)


@router.get("/{transaction_id}", response_model=TransactionRead)
def get_transaction(
    transaction_id: UUID,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> TransactionRead:
    return TransactionService(db, user.id).get_transaction(transaction_id)


@router.put("/{transaction_id}", response_model=TransactionRead)
def update_transaction(
    transaction_id: UUID,
    data: TransactionCreate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> TransactionRead:
    return TransactionService(db, user.id).update_transaction(transaction_id, data)


@router.delete("/{transaction_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_transaction(
    transaction_id: UUID,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Response:
    TransactionService(db, user.id).delete_transaction(transaction_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
