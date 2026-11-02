"""Bills and their optional payment transaction."""

from datetime import date, datetime
from decimal import Decimal
from uuid import UUID, uuid4

from sqlalchemy import Date, DateTime, ForeignKey, Numeric, String, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base


class Bill(Base):
    """A bill tracked by a user and optionally paid from an owned account."""

    __tablename__ = "bills"

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    account_id: Mapped[UUID | None] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("accounts.id", ondelete="SET NULL"), nullable=True
    )
    paid_transaction_id: Mapped[UUID | None] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("transactions.id", ondelete="SET NULL"), nullable=True
    )
    bill_name: Mapped[str] = mapped_column(String(160), nullable=False)
    category: Mapped[str] = mapped_column(String(80), nullable=False)
    amount: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    due_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(20), default="upcoming", nullable=False, index=True)
    recurrence: Mapped[str | None] = mapped_column(String(20))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
