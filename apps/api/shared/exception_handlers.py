from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from shared.exceptions import (
    IdempotencyConflictError,
    LedgerImbalanceError,
    PaymentDeclinedException,
    PaymentNotFoundError,
    ProcessorError,
)


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(LedgerImbalanceError)
    async def ledger_imbalance_handler(request: Request, exc: LedgerImbalanceError):
        return JSONResponse(status_code=400, content={"detail": str(exc)})

    @app.exception_handler(PaymentNotFoundError)
    async def payment_not_found_handler(request: Request, exc: PaymentNotFoundError):
        return JSONResponse(status_code=404, content={"detail": str(exc)})

    @app.exception_handler(IdempotencyConflictError)
    async def idempotency_conflict_handler(
        request: Request, exc: IdempotencyConflictError
    ):
        return JSONResponse(status_code=409, content={"detail": str(exc)})

    @app.exception_handler(ProcessorError)
    async def processor_error_handler(request: Request, exc: ProcessorError):
        return JSONResponse(status_code=502, content={"detail": str(exc)})

    @app.exception_handler(PaymentDeclinedException)
    async def payment_declined_handler(request: Request, exc: PaymentDeclinedException):
        return JSONResponse(status_code=402, content={"detail": str(exc)})
