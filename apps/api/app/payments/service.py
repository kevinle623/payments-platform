import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.ledger import service as ledger_service
from app.payments import repository
from app.payments.schemas import (
    AuthorizeRequest,
    AuthorizeResponse,
    CaptureResponse,
    RefundResponse,
)
from shared.exceptions import PaymentNotFoundError
from shared.logger import logger
from shared.processors.base import PaymentProcessor
from shared.settings import PROCESSOR


async def authorize(
    session: AsyncSession,
    request: AuthorizeRequest,
    processor: PaymentProcessor,
    expense_account_id: uuid.UUID,
    liability_account_id: uuid.UUID,
) -> AuthorizeResponse:
    existing = await repository.get_by_idempotency_key(session, request.idempotency_key)
    if existing:
        return existing

    payment_intent = await processor.create_payment_intent(
        amount=request.amount,
        currency=request.currency,
        metadata=request.metadata,
    )

    try:
        record = await repository.create(
            session,
            idempotency_key=request.idempotency_key,
            amount=request.amount,
            currency=request.currency,
            processor=PROCESSOR,
            processor_payment_id=payment_intent.processor_id,
        )
        await ledger_service.record_authorization(
            session,
            expense_account_id=expense_account_id,
            liability_account_id=liability_account_id,
            amount=request.amount,
            description=f"authorization for payment {record.id}",
        )
        await session.commit()
        return AuthorizeResponse(
            id=record.id,
            processor_payment_id=record.processor_payment_id,
            client_secret=payment_intent.client_secret,
            status=record.status,
            amount=record.amount,
            currency=record.currency,
            idempotency_key=record.idempotency_key,
            created_at=record.created_at,
        )
    except Exception:
        await session.rollback()
        raise


async def capture(
    session: AsyncSession,
    processor_payment_id: str,
    processor: PaymentProcessor,
    liability_account_id: uuid.UUID,
    cash_account_id: uuid.UUID,
) -> CaptureResponse:
    await processor.capture(processor_payment_id)

    try:
        record = await repository.settle(session, processor_payment_id)
        if not record:
            raise PaymentNotFoundError(f"Payment not found: {processor_payment_id}")

        await ledger_service.record_settlement(
            session,
            liability_account_id=liability_account_id,
            cash_account_id=cash_account_id,
            amount=record.amount,
            description=f"settlement for payment {record.id}",
        )
        await session.commit()
        return CaptureResponse(
            id=record.id,
            processor_payment_id=record.processor_payment_id,
            status=record.status,
            amount=record.amount,
            currency=record.currency,
            updated_at=record.updated_at,
        )
    except Exception:
        await session.rollback()
        raise


async def refund(
    session: AsyncSession,
    processor_payment_id: str,
    amount: int,
    processor: PaymentProcessor,
) -> RefundResponse:
    await processor.refund(processor_payment_id, amount)

    try:
        record = await repository.refund_payment(session, processor_payment_id)
        if not record:
            raise PaymentNotFoundError(f"Payment not found: {processor_payment_id}")

        await session.commit()
        return RefundResponse(
            id=record.id,
            processor_payment_id=record.processor_payment_id,
            status=record.status,
            amount=record.amount,
            currency=record.currency,
            updated_at=record.updated_at,
        )
    except Exception:
        await session.rollback()
        raise


async def handle_payment_succeeded(
    session: AsyncSession,
    processor_payment_id: str,
    liability_account_id: uuid.UUID,
    cash_account_id: uuid.UUID,
) -> None:
    try:
        record = await repository.settle(session, processor_payment_id)
        if not record:
            logger.warning(
                "Received payment.succeeded for unknown payment: %s",
                processor_payment_id,
            )
            return

        await ledger_service.record_settlement(
            session,
            liability_account_id=liability_account_id,
            cash_account_id=cash_account_id,
            amount=record.amount,
            description=f"settlement for payment {record.id}",
        )
        await session.commit()
        logger.info("Payment settled: %s", processor_payment_id)
    except Exception:
        await session.rollback()
        raise


async def handle_payment_refunded(
    session: AsyncSession,
    processor_payment_id: str,
) -> None:
    try:
        record = await repository.refund_payment(session, processor_payment_id)
        if not record:
            logger.warning(
                "Received payment.refunded for unknown payment: %s",
                processor_payment_id,
            )
            return
        await session.commit()
        logger.info("Payment refunded: %s", processor_payment_id)
    except Exception:
        await session.rollback()
        raise
