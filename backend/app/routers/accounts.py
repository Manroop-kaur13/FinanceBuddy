"""Account management endpoints."""

from uuid import UUID

from fastapi import APIRouter, Depends, Query, Response, status
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user
from app.database.database import get_db
from app.models.user import User
from app.schemas.account import AccountCreate, AccountRead, AccountUpdate
from app.services.account_service import AccountService

router = APIRouter(prefix="/api/accounts", tags=["Accounts"])


@router.get("", response_model=list[AccountRead])
def list_accounts(
    limit: int = Query(default=100, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[AccountRead]:
    return AccountService(db, user.id).get_accounts(limit=limit, offset=offset)


@router.post("", response_model=AccountRead, status_code=status.HTTP_201_CREATED)
def create_account(
    data: AccountCreate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> AccountRead:
    return AccountService(db, user.id).create_account(data)


@router.get("/{account_id}", response_model=AccountRead)
def get_account(
    account_id: UUID,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> AccountRead:
    return AccountService(db, user.id).get_account(account_id)


@router.put("/{account_id}", response_model=AccountRead)
def update_account(
    account_id: UUID,
    data: AccountUpdate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> AccountRead:
    return AccountService(db, user.id).update_account(account_id, data)


@router.delete("/{account_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_account(
    account_id: UUID,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Response:
    AccountService(db, user.id).delete_account(account_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
