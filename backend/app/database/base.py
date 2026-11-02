"""Base class shared by SQLAlchemy model classes."""

from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """Base metadata container used by Alembic to find database tables."""

