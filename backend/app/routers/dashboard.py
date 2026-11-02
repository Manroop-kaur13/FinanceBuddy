"""Dashboard summary endpoint."""

from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user
from app.database.database import get_db
from app.models.user import User
from app.schemas.analytics import DashboardSummary
from app.services.dashboard_service import DashboardService

router = APIRouter(prefix="/api/dashboard", tags=["Dashboard"])


@router.get("/summary", response_model=DashboardSummary)
def dashboard_summary(
    user: User = Depends(get_current_user), db: Session = Depends(get_db)
) -> DashboardSummary:
    return DashboardService(db, user.id).get_summary()
