"""SQLAlchemy engine, session factory, and request-scoped database session."""

from collections.abc import Generator

from fastapi import HTTPException, status
from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import get_settings


def create_database_engine() -> Engine | None:
    """Create the PostgreSQL engine when DATABASE_URL has been configured."""
    database_url = get_settings().database_url
    if not database_url:
        return None

    # Neon and most hosted providers supply postgresql:// URLs. This project
    # installs psycopg 3, so select its SQLAlchemy dialect explicitly.
    if database_url.startswith("postgres://"):
        database_url = database_url.replace("postgres://", "postgresql+psycopg://", 1)
    elif database_url.startswith("postgresql://"):
        database_url = database_url.replace("postgresql://", "postgresql+psycopg://", 1)

    return create_engine(database_url, pool_pre_ping=True)


engine = create_database_engine()
SessionLocal = (
    sessionmaker(bind=engine, autoflush=False, autocommit=False)
    if engine is not None
    else None
)


def get_db() -> Generator[Session, None, None]:
    """Yield one database session for an API request, then always close it."""
    if SessionLocal is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database is not configured. Set DATABASE_URL in backend/.env.",
        )

    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
