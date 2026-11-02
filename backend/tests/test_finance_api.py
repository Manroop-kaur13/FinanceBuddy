"""API-level checks for financial rules and user isolation."""

from datetime import date
from decimal import Decimal

from sqlalchemy import select

from app.models.user import User
from app.services.loan_service import LoanService


def register_and_login(client, email: str = "owner@example.com") -> dict[str, str]:
    response = client.post(
        "/api/auth/register",
        json={"name": "Test Owner", "email": email, "password": "Test-Password-42!"},
    )
    assert response.status_code == 201, response.text
    login = client.post(
        "/api/auth/login",
        json={"email": email, "password": "Test-Password-42!"},
    )
    assert login.status_code == 200, login.text
    return {"Authorization": f"Bearer {login.json()['access_token']}"}


def create_account(client, headers, name="Main", kind="bank", opening="1000.00"):
    response = client.post(
        "/api/accounts",
        headers=headers,
        json={
            "account_name": name,
            "account_type": kind,
            "currency": "INR",
            "opening_balance": opening,
        },
    )
    assert response.status_code == 201, response.text
    return response.json()


def test_registration_login_and_logout_revoke_token(client, db_session):
    headers = register_and_login(client)
    profile = client.get("/api/users/me", headers=headers)
    assert profile.status_code == 200
    assert "hashed_password" not in profile.json()

    user = db_session.scalar(select(User).where(User.email == "owner@example.com"))
    assert user is not None
    assert user.hashed_password != "Test-Password-42!"
    assert user.hashed_password.startswith("$argon2")

    wrong_login = client.post(
        "/api/auth/login", json={"email": user.email, "password": "wrong-password"}
    )
    assert wrong_login.status_code == 401

    logout = client.post("/api/auth/logout", headers=headers)
    assert logout.status_code == 200
    assert client.get("/api/users/me", headers=headers).status_code == 401


def test_income_expense_transfer_update_delete_balance(client):
    headers = register_and_login(client)
    source = create_account(client, headers, opening="100.00")
    destination = create_account(client, headers, name="Savings", kind="savings", opening="40.00")

    income = client.post(
        "/api/transactions",
        headers=headers,
        json={
            "account_id": source["id"], "transaction_type": "income", "amount": "50.00",
            "category": "Salary", "description": "Pay", "transaction_date": "2026-11-01",
        },
    )
    assert income.status_code == 201, income.text
    expense = client.post(
        "/api/transactions",
        headers=headers,
        json={
            "account_id": source["id"], "transaction_type": "expense", "amount": "10.00",
            "category": "Food", "description": "Lunch", "transaction_date": "2026-11-02",
        },
    )
    assert expense.status_code == 201, expense.text
    transfer = client.post(
        "/api/transactions",
        headers=headers,
        json={
            "account_id": source["id"], "destination_account_id": destination["id"],
            "transaction_type": "transfer", "amount": "25.00", "category": "Transfer",
            "description": "Move money", "transaction_date": "2026-11-02",
        },
    )
    assert transfer.status_code == 201, transfer.text
    assert client.get(f"/api/accounts/{source['id']}", headers=headers).json()["current_balance"] == "115.00"
    assert client.get(f"/api/accounts/{destination['id']}", headers=headers).json()["current_balance"] == "65.00"

    corrected = client.put(
        f"/api/transactions/{expense.json()['id']}",
        headers=headers,
        json={
            "account_id": source["id"], "transaction_type": "expense", "amount": "15.00",
            "category": "Food", "description": "Lunch", "transaction_date": "2026-11-02",
        },
    )
    assert corrected.status_code == 200, corrected.text
    assert client.get(f"/api/accounts/{source['id']}", headers=headers).json()["current_balance"] == "110.00"
    deleted = client.delete(f"/api/transactions/{expense.json()['id']}", headers=headers)
    assert deleted.status_code == 204
    assert client.get(f"/api/accounts/{source['id']}", headers=headers).json()["current_balance"] == "125.00"


def test_invalid_amount_and_transfer_shape_are_rejected(client):
    headers = register_and_login(client)
    account = create_account(client, headers)
    invalid = client.post(
        "/api/transactions",
        headers=headers,
        json={
            "account_id": account["id"], "transaction_type": "expense", "amount": "0",
            "category": "Food", "description": "No amount", "transaction_date": "2026-11-01",
        },
    )
    assert invalid.status_code == 422
    missing_destination = client.post(
        "/api/transactions",
        headers=headers,
        json={
            "account_id": account["id"], "transaction_type": "transfer", "amount": "1",
            "category": "Transfer", "description": "Bad transfer", "transaction_date": "2026-11-01",
        },
    )
    assert missing_destination.status_code == 422


def test_user_cannot_read_another_users_account(client):
    first_headers = register_and_login(client, "first@example.com")
    account = create_account(client, first_headers)
    second_headers = register_and_login(client, "second@example.com")
    assert client.get(f"/api/accounts/{account['id']}", headers=second_headers).status_code == 404
    assert client.get("/api/accounts", headers=second_headers).json() == []


def test_bill_payment_is_atomic_and_not_repeatable(client):
    headers = register_and_login(client)
    account = create_account(client, headers, opening="500.00")
    bill = client.post(
        "/api/bills",
        headers=headers,
        json={
            "bill_name": "Electricity", "category": "Utilities", "amount": "125.00",
            "due_date": "2026-11-10", "account_id": account["id"],
        },
    )
    assert bill.status_code == 201, bill.text
    paid = client.post(f"/api/bills/{bill.json()['id']}/pay", headers=headers, json={})
    assert paid.status_code == 200, paid.text
    assert paid.json()["status"] == "paid"
    assert client.get(f"/api/accounts/{account['id']}", headers=headers).json()["current_balance"] == "375.00"
    duplicate = client.post(f"/api/bills/{bill.json()['id']}/pay", headers=headers, json={})
    assert duplicate.status_code == 409
    assert len(client.get("/api/transactions", headers=headers).json()) == 1


def test_budget_uses_expenses_but_not_transfers(client):
    headers = register_and_login(client)
    source = create_account(client, headers, opening="500.00")
    destination = create_account(client, headers, name="Savings", kind="savings", opening="0.00")
    for kind, amount, category, dest in [
        ("expense", "30.00", "Food", None),
        ("transfer", "80.00", "Move", destination["id"]),
    ]:
        payload = {
            "account_id": source["id"], "transaction_type": kind, "amount": amount,
            "category": category, "description": category, "transaction_date": "2026-11-02",
        }
        if dest:
            payload["destination_account_id"] = dest
        assert client.post("/api/transactions", headers=headers, json=payload).status_code == 201
    budget = client.post(
        "/api/budgets", headers=headers,
        json={"category": "Food", "budget_limit": "100.00", "period": "monthly", "start_date": "2026-01-01"},
    )
    assert budget.status_code == 201, budget.text
    progress = client.get(f"/api/budgets/{budget.json()['id']}/progress", headers=headers)
    assert progress.status_code == 200
    assert progress.json()["spent"] == "30.00"
    assert progress.json()["remaining"] == "70.00"


def test_goal_contribution_and_emi_formula(client):
    headers = register_and_login(client)
    goal = client.post(
        "/api/goals", headers=headers,
        json={"goal_name": "Emergency fund", "target_amount": "100.00", "target_date": "2027-11-01"},
    )
    contribution = client.post(
        f"/api/goals/{goal.json()['id']}/contributions", headers=headers, json={"amount": "120.00"}
    )
    assert contribution.status_code == 200
    assert contribution.json()["current_amount"] == "100.00"
    assert contribution.json()["status"] == "completed"
    assert LoanService.calculate_emi(Decimal("10000"), Decimal("12"), 12) == Decimal("888.49")
    assert LoanService.calculate_emi(Decimal("1200"), Decimal("0"), 12) == Decimal("100.00")


def test_credit_card_purchase_and_payment_accounting(client):
    headers = register_and_login(client)
    bank = create_account(client, headers, opening="2000.00")
    card_account = create_account(client, headers, name="Card", kind="credit_card", opening="0.00")
    card = client.post(
        "/api/credit-cards", headers=headers,
        json={"account_id": card_account["id"], "card_name": "Travel Card", "credit_limit": "5000.00", "billing_cycle": 15},
    )
    assert card.status_code == 201, card.text
    expense = client.post(
        f"/api/credit-cards/{card.json()['id']}/expenses", headers=headers,
        json={"amount": "1250.00", "category": "Travel", "description": "Flight", "transaction_date": "2026-11-02"},
    )
    assert expense.status_code == 201, expense.text
    assert client.get(f"/api/credit-cards/{card.json()['id']}", headers=headers).json()["outstanding_amount"] == "1250.00"
    payment = client.post(
        f"/api/credit-cards/{card.json()['id']}/payments", headers=headers,
        json={"source_account_id": bank["id"], "amount": "300.00", "payment_date": "2026-11-02"},
    )
    assert payment.status_code == 201, payment.text
    assert payment.json()["transaction_type"] == "transfer"
    assert client.get(f"/api/credit-cards/{card.json()['id']}", headers=headers).json()["outstanding_amount"] == "950.00"
    assert client.get("/api/transactions?transaction_type=expense", headers=headers).json()[0]["amount"] == "1250.00"


def test_investment_portfolio_uses_saved_prices(client):
    headers = register_and_login(client)
    created = client.post(
        "/api/investments", headers=headers,
        json={
            "investment_name": "Index fund", "investment_type": "mutual_fund", "quantity": "2",
            "purchase_price": "10.00", "current_price": "12.00", "purchase_date": "2026-01-01",
        },
    )
    assert created.status_code == 201, created.text
    summary = client.get("/api/investments/portfolio", headers=headers)
    assert summary.status_code == 200
    assert summary.json()["total_value"] == "24.00"
    assert summary.json()["total_gain_loss"] == "4.00"


def test_account_balance_and_dashboard_are_database_backed(client):
    headers = register_and_login(client)
    account = create_account(client, headers, opening="300.00")
    client.post(
        "/api/transactions", headers=headers,
        json={
            "account_id": account["id"], "transaction_type": "income", "amount": "200.00",
            "category": "Salary", "description": "Pay", "transaction_date": date.today().isoformat(),
        },
    )
    summary = client.get("/api/dashboard/summary", headers=headers)
    assert summary.status_code == 200, summary.text
    assert summary.json()["total_balance"] == "500.00"
    assert summary.json()["total_income"] == "200.00"
