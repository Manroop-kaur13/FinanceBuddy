"""Investment holdings and current valuations."""

from datetime import date, datetime
from decimal import Decimal
from uuid import UUID, uuid4

from sqlalchemy import Date, DateTime, ForeignKey, Numeric, String, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base


class Investment(Base):
    """A quantity of an investment asset held by a user."""

    __tablename__ = "investments"

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    investment_name: Mapped[str] = mapped_column(String(160), nullable=False)
    investment_type: Mapped[str] = mapped_column(String(60), nullable=False)
    quantity: Mapped[Decimal] = mapped_column(Numeric(20, 8), nullable=False)
    purchase_price: Mapped[Decimal] = mapped_column(Numeric(14, 4), nullable=False)
    current_price: Mapped[Decimal] = mapped_column(Numeric(14, 4), nullable=False)
    purchase_date: Mapped[date] = mapped_column(Date, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
