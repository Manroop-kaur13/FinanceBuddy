"""Credit-card management, purchase, payment, and statement endpoints."""

from datetime import date
from uuid import UUID

from fastapi import APIRouter, Depends, Query, Response, status
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user
from app.database.database import get_db
from app.models.user import User
from app.schemas.credit_card import (
    CardExpenseCreate,
    CardPaymentCreate,
    CreditCardCreate,
    CreditCardRead,
    CreditCardUpdate,
)
from app.schemas.transaction import TransactionRead
from app.services.credit_card_service import CreditCardService

router = APIRouter(prefix="/api/credit-cards", tags=["Credit cards"])


@router.get("", response_model=list[CreditCardRead])
def list_cards(
    limit: int = Query(default=100, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[CreditCardRead]:
    return CreditCardService(db, user.id).get_credit_cards(limit=limit, offset=offset)


@router.post("", response_model=CreditCardRead, status_code=status.HTTP_201_CREATED)
def create_card(
    data: CreditCardCreate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> CreditCardRead:
    return CreditCardService(db, user.id).add_credit_card(data)


@router.get("/{card_id}/statement", response_model=list[TransactionRead])
def card_statement(
    card_id: UUID,
    date_from: date | None = None,
    date_to: date | None = None,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[TransactionRead]:
    return CreditCardService(db, user.id).get_statement(
        card_id, date_from=date_from, date_to=date_to
    )


@router.post("/{card_id}/expenses", response_model=TransactionRead, status_code=status.HTTP_201_CREATED)
def record_card_expense(
    card_id: UUID,
    data: CardExpenseCreate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> TransactionRead:
    return CreditCardService(db, user.id).record_card_expense(card_id, data)


@router.post("/{card_id}/payments", response_model=TransactionRead, status_code=status.HTTP_201_CREATED)
def record_card_payment(
    card_id: UUID,
    data: CardPaymentCreate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> TransactionRead:
    return CreditCardService(db, user.id).record_card_payment(card_id, data)


@router.get("/{card_id}", response_model=CreditCardRead)
def get_card(
    card_id: UUID, user: User = Depends(get_current_user), db: Session = Depends(get_db)
) -> CreditCardRead:
    service = CreditCardService(db, user.id)
    return service._read(service.get_credit_card(card_id))


@router.put("/{card_id}", response_model=CreditCardRead)
def update_card(
    card_id: UUID,
    data: CreditCardUpdate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> CreditCardRead:
    return CreditCardService(db, user.id).update_credit_card(card_id, data)


@router.delete("/{card_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_card(
    card_id: UUID,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Response:
    CreditCardService(db, user.id).delete_credit_card(card_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
