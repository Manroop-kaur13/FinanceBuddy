"""Investment holdings and portfolio summary endpoints."""

from uuid import UUID

from fastapi import APIRouter, Depends, Query, Response, status
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user
from app.database.database import get_db
from app.models.user import User
from app.schemas.investment import InvestmentCreate, InvestmentRead, InvestmentUpdate, PortfolioSummary
from app.services.investment_service import InvestmentService

router = APIRouter(prefix="/api/investments", tags=["Investments"])


@router.get("", response_model=list[InvestmentRead])
def list_investments(
    limit: int = Query(default=100, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[InvestmentRead]:
    return InvestmentService(db, user.id).get_investments(limit=limit, offset=offset)


@router.get("/portfolio", response_model=PortfolioSummary)
def portfolio_summary(
    user: User = Depends(get_current_user), db: Session = Depends(get_db)
) -> PortfolioSummary:
    return InvestmentService(db, user.id).get_portfolio_summary()


@router.post("", response_model=InvestmentRead, status_code=status.HTTP_201_CREATED)
def create_investment(
    data: InvestmentCreate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> InvestmentRead:
    return InvestmentService(db, user.id).add_investment(data)


@router.get("/{investment_id}", response_model=InvestmentRead)
def get_investment(
    investment_id: UUID,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> InvestmentRead:
    return InvestmentService(db, user.id).get_owned(investment_id)


@router.put("/{investment_id}", response_model=InvestmentRead)
def update_investment(
    investment_id: UUID,
    data: InvestmentUpdate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> InvestmentRead:
    return InvestmentService(db, user.id).update_investment(investment_id, data)


@router.delete("/{investment_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_investment(
    investment_id: UUID,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Response:
    InvestmentService(db, user.id).delete_investment(investment_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
