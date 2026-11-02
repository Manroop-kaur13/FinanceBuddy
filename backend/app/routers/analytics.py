"""Cash-flow and spending analytics endpoints."""

from datetime import date
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user
from app.database.database import get_db
from app.models.user import User
from app.schemas.analytics import CashFlowMonth, CategorySpending
from app.services.analytics_service import AnalyticsService

router = APIRouter(prefix="/api/analytics", tags=["Analytics"])


@router.get("/cash-flow", response_model=list[CashFlowMonth])
def cash_flow(
    months: int = Query(default=6, ge=1, le=36),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[CashFlowMonth]:
    return AnalyticsService(db, user.id).monthly_cash_flow(months=months)


@router.get("/category-spending", response_model=list[CategorySpending])
def category_spending(
    date_from: date | None = None,
    date_to: date | None = None,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[CategorySpending]:
    return AnalyticsService(db, user.id).spending_by_category(
        date_from=date_from, date_to=date_to
    )
