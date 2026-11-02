# FinanceBuddy API

FastAPI backend for the existing FinanceBuddy frontend. It uses PostgreSQL (Neon is supported), SQLAlchemy, Alembic, and revocable JWT sessions.

## Included modules

- Registration, login, logout, profile read/update, and account deletion. Passwords use Argon2; protected requests validate the active session in PostgreSQL.
- Accounts, income/expense/transfer transactions, bill payments, category budgets, savings goals, loans and EMI payments, credit cards and payments, investment portfolio records, recurring transaction schedules, and document metadata.
- Database-backed dashboard and analytics endpoints.

All financial records are scoped to the authenticated user. Money values use decimal database columns. Transfers are excluded from income/expense summaries.

## Local setup

From this folder in PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements-dev.txt
Copy-Item .env.example .env
```

Set `DATABASE_URL` to the Neon PostgreSQL connection string and `JWT_SECRET_KEY` to a random private value in `.env`. Do not commit or share `.env`. Set `CORS_ORIGINS` to a comma-separated list of exact frontend origins, for example `http://localhost:3000,https://finance-buddyai.vercel.app`.

Apply migrations and run the API:

```powershell
alembic upgrade head
alembic current
uvicorn app.main:app --reload
```

Interactive API docs are at http://127.0.0.1:8000/docs; health check is `GET /api/health`.

## API routes

All business routes except health and registration/login require `Authorization: Bearer <access_token>`. OpenAPI at `/docs` lists request and response fields.

| Prefix | Functionality |
|---|---|
| `/api/auth`, `/api/users` | Register/login/logout and current profile |
| `/api/accounts` | List, create, view, update, delete accounts and balances |
| `/api/transactions` | Filter, create, edit, and delete transactions |
| `/api/bills` | Bill schedules, upcoming bills, and one-time payment |
| `/api/budgets` | Budgets and period spending progress |
| `/api/goals` | Goals and contributions |
| `/api/loans` | Loans, EMI calculation, and payments |
| `/api/credit-cards` | Cards, purchases, and payments |
| `/api/investments` | Investment records and portfolio summary |
| `/api/recurring-transactions` | Recurring schedule records |
| `/api/documents` | Document metadata records |
| `/api/dashboard`, `/api/analytics` | Summary, cash flow, category breakdowns |

## Tests

Install development dependencies and run `python -m pytest -q`. Tests use an isolated in-memory SQLite database and do not modify Neon.

## Current boundaries

Recurring schedules are stored and exposed through the API; a background job to execute them is not included. Documents store metadata and a storage key; binary uploads require a configured object-storage provider. Investment prices are the values last saved by the user; there is no market-price feed. Dashboard totals do not perform foreign-exchange conversion, so use a consistent currency for accounts and records included in totals.
