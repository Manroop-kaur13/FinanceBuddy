"""Bill CRUD and atomic bill payment operations."""

from datetime import date
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.account import Account
from app.models.bill import Bill
from app.schemas.bill import BillCreate, BillUpdate
from app.schemas.transaction import TransactionCreate
from app.services.base import OwnedService
from app.services.transaction_service import TransactionService


class BillService(OwnedService):
    """Manage bills and create exactly one expense when a bill is paid."""

    model = Bill

    def __init__(self, db: Session, user_id: UUID) -> None:
        super().__init__(db, user_id)

    def _validate_account(self, account_id: UUID | None) -> None:
        if account_id is not None and self.db.scalar(
            select(Account.id).where(Account.id == account_id, Account.user_id == self.user_id)
        ) is None:
            raise HTTPException(status_code=404, detail="Account not found.")

    def create_bill(self, data: BillCreate) -> Bill:
        self._validate_account(data.account_id)
        bill = Bill(user_id=self.user_id, **data.model_dump())
        self.db.add(bill)
        self.db.commit()
        self.db.refresh(bill)
        return bill

    def get_bills(self, *, limit: int = 100, offset: int = 0) -> list[Bill]:
        return self.list_owned(limit=limit, offset=offset)

    def update_bill(self, bill_id: UUID, data: BillUpdate) -> Bill:
        bill = self.get_owned(bill_id)
        self._validate_account(data.account_id)
        if bill.status == "paid":
            raise HTTPException(status_code=409, detail="Paid bills cannot be edited.")
        self.apply_updates(bill, data)
        self.db.commit()
        self.db.refresh(bill)
        return bill

    def delete_bill(self, bill_id: UUID) -> None:
        bill = self.get_owned(bill_id)
        if bill.status == "paid":
            raise HTTPException(status_code=409, detail="Paid bills cannot be deleted.")
        self.db.delete(bill)
        self.db.commit()

    def mark_bill_paid(self, bill_id: UUID, *, account_id: UUID | None = None) -> Bill:
        bill = self.get_owned(bill_id)
        if bill.status == "paid" or bill.paid_transaction_id is not None:
            raise HTTPException(status_code=409, detail="This bill has already been paid.")
        payment_account_id = account_id or bill.account_id
        if payment_account_id is None:
            raise HTTPException(status_code=422, detail="Choose an account to pay this bill from.")
        self._validate_account(payment_account_id)
        transaction = TransactionService(self.db, self.user_id).add_transaction(
            TransactionCreate(
                account_id=payment_account_id,
                transaction_type="expense",
                amount=bill.amount,
                category=bill.category,
                description=f"Bill payment: {bill.bill_name}",
                transaction_date=date.today(),
                merchant=bill.bill_name,
            ),
            commit=False,
        )
        bill.status = "paid"
        bill.account_id = payment_account_id
        bill.paid_transaction_id = transaction.id
        self.db.commit()
        self.db.refresh(bill)
        return bill

    def get_upcoming_bills(self, *, through: date, limit: int = 100) -> list[Bill]:
        return list(
            self.db.scalars(
                select(Bill)
                .where(
                    Bill.user_id == self.user_id,
                    Bill.status != "paid",
                    Bill.due_date >= date.today(),
                    Bill.due_date <= through,
                )
                .order_by(Bill.due_date)
                .limit(limit)
            ).all()
        )

    def get_overdue_bills(self, *, today: date | None = None) -> list[Bill]:
        cutoff = today or date.today()
        return list(
            self.db.scalars(
                select(Bill)
                .where(Bill.user_id == self.user_id, Bill.status != "paid", Bill.due_date < cutoff)
                .order_by(Bill.due_date)
            ).all()
        )
