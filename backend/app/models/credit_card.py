"""Credit card limits and statement metadata."""

from datetime import date, datetime
from decimal import Decimal
from uuid import UUID, uuid4

from sqlalchemy import Date, DateTime, ForeignKey, Numeric, String, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base


class CreditCard(Base):
    """Credit facility linked to an account used for card transactions."""

    __tablename__ = "credit_cards"

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    account_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("accounts.id", ondelete="CASCADE"), unique=True
    )
    card_name: Mapped[str] = mapped_column(String(120), nullable=False)
    credit_limit: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    outstanding_amount: Mapped[Decimal] = mapped_column(
        Numeric(14, 2), default=0, server_default="0", nullable=False
    )
    billing_cycle: Mapped[int] = mapped_column(nullable=False)
    due_date: Mapped[date | None] = mapped_column(Date)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
