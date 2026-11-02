from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import get_settings

from app.routers.auth import router as auth_router
from app.routers.accounts import router as accounts_router
from app.routers.analytics import router as analytics_router
from app.routers.bills import router as bills_router
from app.routers.budgets import router as budgets_router
from app.routers.credit_cards import router as credit_cards_router
from app.routers.dashboard import router as dashboard_router
from app.routers.documents import router as documents_router
from app.routers.goals import router as goals_router
from app.routers.health import router as health_router
from app.routers.investments import router as investments_router
from app.routers.loans import router as loans_router
from app.routers.recurring_transactions import router as recurring_router
from app.routers.transactions import router as transactions_router
from app.routers.users import router as users_router

app = FastAPI(
    title="FinanceBuddy API",
    description="Backend API for the FinanceBuddy personal finance application.",
    version="0.1.0",
)

settings = get_settings()
app.add_middleware(
    CORSMiddleware,
    allow_origins=[origin.strip() for origin in settings.cors_origins.split(",") if origin.strip()],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health_router)
app.include_router(auth_router)
app.include_router(users_router)
app.include_router(accounts_router)
app.include_router(transactions_router)
app.include_router(bills_router)
app.include_router(budgets_router)
app.include_router(goals_router)
app.include_router(loans_router)
app.include_router(credit_cards_router)
app.include_router(investments_router)
app.include_router(recurring_router)
app.include_router(documents_router)
app.include_router(dashboard_router)
app.include_router(analytics_router)
