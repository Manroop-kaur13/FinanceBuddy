"""Loan balances and recorded EMI payments."""

from datetime import date, datetime
from decimal import Decimal
from uuid import UUID, uuid4

from sqlalchemy import Date, DateTime, ForeignKey, Numeric, String, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base


class Loan(Base):
    """A reducing-balance loan with a calculated EMI."""

    __tablename__ = "loans"

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    loan_name: Mapped[str] = mapped_column(String(160), nullable=False)
    principal: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    interest_rate: Mapped[Decimal] = mapped_column(Numeric(7, 4), nullable=False)
    tenure_months: Mapped[int] = mapped_column(nullable=False)
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    emi_amount: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    outstanding_balance: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="active", nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class LoanPayment(Base):
    """A loan payment linked to its expense transaction for auditability."""

    __tablename__ = "loan_payments"

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    loan_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("loans.id", ondelete="CASCADE"), index=True
    )
    transaction_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("transactions.id", ondelete="CASCADE"), unique=True
    )
    amount: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    principal_paid: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    interest_paid: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    payment_date: Mapped[date] = mapped_column(Date, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
