from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.payments.router import router as payments_router
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


@app.get("/_live")
async def liveness():
    return {"status": "ok"}
