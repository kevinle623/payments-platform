from fastapi import FastAPI

from app.payments.router import router as payments_router
from shared.exception_handlers import register_exception_handlers

app = FastAPI(title="Payments Platform")

register_exception_handlers(app)
app.include_router(payments_router)


@app.get("/_live")
async def liveness():
    return {"status": "ok"}
