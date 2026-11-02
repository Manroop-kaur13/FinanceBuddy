"""Health endpoints for the API and its PostgreSQL connection."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.database.database import get_db

router = APIRouter(prefix="/api/health", tags=["Health"])


@router.get("")
def health_check() -> dict[str, str]:
    """Report whether the API process is responding."""
    return {"status": "ok", "service": "FinanceBuddy API"}


@router.get("/database")
def database_health_check(db: Session = Depends(get_db)) -> dict[str, str]:
    """Run a lightweight query to verify the configured database connection."""
    try:
        db.execute(text("SELECT 1"))
    except SQLAlchemyError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database connection failed. Check DATABASE_URL and network access.",
        ) from exc

    return {"status": "ok", "database": "connected"}
