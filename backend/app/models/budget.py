"""Spending budgets grouped by category and period."""

from datetime import date, datetime
from decimal import Decimal
from uuid import UUID, uuid4

from sqlalchemy import Date, DateTime, ForeignKey, Numeric, String, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base


class Budget(Base):
    """A user-defined category spending limit."""

    __tablename__ = "budgets"

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    category: Mapped[str] = mapped_column(String(80), nullable=False, index=True)
    budget_limit: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    period: Mapped[str] = mapped_column(String(20), default="monthly", nullable=False)
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
