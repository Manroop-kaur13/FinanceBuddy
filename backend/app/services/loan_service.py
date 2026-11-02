"""Loan CRUD, EMI calculations, schedules, and payment processing."""

import calendar
from datetime import date
from decimal import Decimal, ROUND_HALF_UP
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.loan import Loan, LoanPayment
from app.schemas.loan import (
    EmiScheduleItem,
    LoanCreate,
    LoanPaymentCreate,
    LoanPaymentRead,
    LoanUpdate,
)
from app.schemas.transaction import TransactionCreate
from app.services.base import OwnedService
from app.services.transaction_service import TransactionService

CENT = Decimal("0.01")


def add_months(start: date, months: int) -> date:
    """Add whole months while keeping the day within the destination month."""
    month_index = start.month - 1 + months
    year = start.year + month_index // 12
    month = month_index % 12 + 1
    day = min(start.day, calendar.monthrange(year, month)[1])
    return date(year, month, day)


class LoanService(OwnedService):
    """Manage loans using a reducing-balance EMI calculation."""

    model = Loan

    def __init__(self, db: Session, user_id: UUID) -> None:
        super().__init__(db, user_id)

    @staticmethod
    def calculate_emi(principal: Decimal, annual_rate: Decimal, months: int) -> Decimal:
        """Calculate EMI: P*r*(1+r)^n / ((1+r)^n - 1), rounded to cents.

        Here P is principal, r is annual percentage rate / 1200, and n is
        the number of monthly payments. At 0% interest, EMI is P / n.
        """
        if principal <= 0 or months <= 0 or annual_rate < 0:
            raise ValueError("Principal and months must be positive; rate cannot be negative.")
        monthly_rate = annual_rate / Decimal("1200")
        if monthly_rate == 0:
            return (principal / months).quantize(CENT, rounding=ROUND_HALF_UP)
        factor = (Decimal("1") + monthly_rate) ** months
        emi = principal * monthly_rate * factor / (factor - Decimal("1"))
        return emi.quantize(CENT, rounding=ROUND_HALF_UP)

    def create_loan(self, data: LoanCreate) -> Loan:
        emi = self.calculate_emi(data.principal, data.interest_rate, data.tenure_months)
        loan = Loan(
            user_id=self.user_id,
            **data.model_dump(),
            emi_amount=emi,
            outstanding_balance=data.principal,
            status="active",
        )
        self.db.add(loan)
        self.db.commit()
        self.db.refresh(loan)
        return loan

    def get_loans(self, *, limit: int = 100, offset: int = 0) -> list[Loan]:
        return self.list_owned(limit=limit, offset=offset)

    def update_loan(self, loan_id: UUID, data: LoanUpdate) -> Loan:
        loan = self.get_owned(loan_id)
        payment_exists = self.db.scalar(
            select(LoanPayment.id).where(LoanPayment.loan_id == loan_id).limit(1)
        )
        if payment_exists:
            raise HTTPException(status_code=409, detail="Loan terms cannot be edited after payments.")
        values = data.model_dump(exclude_unset=True)
        for field, value in values.items():
            if value is not None:
                setattr(loan, field, value)
        loan.emi_amount = self.calculate_emi(
            loan.principal, loan.interest_rate, loan.tenure_months
        )
        self.db.commit()
        self.db.refresh(loan)
        return loan

    def delete_loan(self, loan_id: UUID) -> None:
        loan = self.get_owned(loan_id)
        has_payments = self.db.scalar(
            select(LoanPayment.id).where(LoanPayment.loan_id == loan_id).limit(1)
        )
        if has_payments:
            raise HTTPException(status_code=409, detail="Loans with payment history cannot be deleted.")
        self.db.delete(loan)
        self.db.commit()

    def generate_emi_schedule(self, loan_id: UUID) -> list[EmiScheduleItem]:
        loan = self.get_owned(loan_id)
        outstanding = loan.principal
        monthly_rate = loan.interest_rate / Decimal("1200")
        schedule: list[EmiScheduleItem] = []
        for installment in range(1, loan.tenure_months + 1):
            interest = (outstanding * monthly_rate).quantize(CENT, rounding=ROUND_HALF_UP)
            payment = loan.emi_amount
            principal_paid = min(outstanding, payment - interest)
            if installment == loan.tenure_months:
                principal_paid = outstanding
                payment = principal_paid + interest
            outstanding = max(Decimal("0.00"), outstanding - principal_paid)
            schedule.append(
                EmiScheduleItem(
                    installment_number=installment,
                    payment_date=add_months(loan.start_date, installment),
                    emi_amount=payment,
                    principal_paid=principal_paid,
                    interest_paid=interest,
                    outstanding_balance=outstanding,
                )
            )
        return schedule

    def record_emi_payment(self, loan_id: UUID, data: LoanPaymentCreate) -> LoanPayment:
        loan = self.get_owned(loan_id)
        if loan.outstanding_balance <= 0:
            raise HTTPException(status_code=409, detail="This loan is already paid off.")
        monthly_rate = loan.interest_rate / Decimal("1200")
        interest = (loan.outstanding_balance * monthly_rate).quantize(CENT, rounding=ROUND_HALF_UP)
        amount = min(loan.emi_amount, loan.outstanding_balance + interest)
        principal_paid = min(loan.outstanding_balance, amount - interest)
        interest_paid = amount - principal_paid

        transaction = TransactionService(self.db, self.user_id).add_transaction(
            TransactionCreate(
                account_id=data.account_id,
                transaction_type="expense",
                amount=amount,
                category="Loan payment",
                description=f"EMI payment: {loan.loan_name}",
                transaction_date=data.payment_date,
            ),
            commit=False,
        )
        loan.outstanding_balance = max(Decimal("0.00"), loan.outstanding_balance - principal_paid)
        if loan.outstanding_balance == 0:
            loan.status = "paid_off"
        payment = LoanPayment(
            user_id=self.user_id,
            loan_id=loan.id,
            transaction_id=transaction.id,
            amount=amount,
            principal_paid=principal_paid,
            interest_paid=interest_paid,
            payment_date=data.payment_date,
        )
        self.db.add(payment)
        self.db.commit()
        self.db.refresh(payment)
        return payment

    def get_outstanding_balance(self, loan_id: UUID) -> Decimal:
        return self.get_owned(loan_id).outstanding_balance

    def get_payments(self, loan_id: UUID) -> list[LoanPayment]:
        loan = self.get_owned(loan_id)
        return list(
            self.db.scalars(
                select(LoanPayment)
                .where(LoanPayment.loan_id == loan.id, LoanPayment.user_id == self.user_id)
                .order_by(LoanPayment.payment_date)
            ).all()
        )
