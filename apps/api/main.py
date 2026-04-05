from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.bills.router import router as bills_router
from app.fraud.router import router as fraud_router
from app.issuer.cards.router import router as issuer_router
from app.payees.router import router as payees_router
from app.payments.router import router as payments_router
from app.reconciliation.router import router as reconciliation_router
from app.reporting.router import router as reporting_router
from shared.exception_handlers import register_exception_handlers

app = FastAPI(title="Payments Platform")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

register_exception_handlers(app)
app.include_router(payments_router)
app.include_router(payees_router)
app.include_router(bills_router)
app.include_router(issuer_router)
app.include_router(fraud_router)
app.include_router(reconciliation_router)
app.include_router(reporting_router)


@app.get("/_live")
async def liveness():
    return {"status": "ok"}
