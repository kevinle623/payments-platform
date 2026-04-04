import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.issuer.auth import service as issuer_auth_service
from app.issuer.auth.models import IssuerAuthDecision
from app.issuer.settlement import service as issuer_settlement_service
from app.ledger import service as ledger_service
from app.outbox import service as outbox_service
from app.outbox.models import OutboxEventType
from app.payments import repository
from app.payments.schemas import (
    AuthorizeRequest,
    AuthorizeResponse,
    CaptureResponse,
    RefundResponse,
)
from shared.exceptions import PaymentDeclinedException, PaymentNotFoundError
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
        logger.info(
            "authorize idempotency hit | idempotency_key=%s payment_id=%s",
            request.idempotency_key,
            existing.id,
        )
        return existing

    issuer_auth = await issuer_auth_service.evaluate(
        session,
        idempotency_key=request.idempotency_key,
        amount=request.amount,
        currency=request.currency,
        metadata=request.metadata,
        card_id=request.card_id,
    )
    if issuer_auth.decision == IssuerAuthDecision.DECLINED:
        logger.warning(
            "issuer declined payment | idempotency_key=%s reason=%s",
            request.idempotency_key,
            issuer_auth.decline_reason,
        )
        raise PaymentDeclinedException(
            issuer_auth.decline_reason or "payment declined by issuer"
        )

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
        await outbox_service.publish_event(
            session,
            event_type=OutboxEventType.PAYMENT_AUTHORIZED,
            payload={
                "payment_id": str(record.id),
                "processor_payment_id": record.processor_payment_id,
                "amount": record.amount,
                "currency": record.currency,
                "idempotency_key": record.idempotency_key,
            },
        )
        await session.commit()
        logger.info(
            "payment authorized | payment_id=%s processor_payment_id=%s amount=%d currency=%s",
            record.id,
            record.processor_payment_id,
            record.amount,
            record.currency,
        )
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
        logger.exception(
            "authorize failed, rolling back | idempotency_key=%s",
            request.idempotency_key,
        )
        await session.rollback()
        raise


async def capture(
    session: AsyncSession,
    processor_payment_id: str,
    processor: PaymentProcessor,
    liability_account_id: uuid.UUID,
    cash_account_id: uuid.UUID,
) -> CaptureResponse:
    logger.info("capturing payment | processor_payment_id=%s", processor_payment_id)
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
        logger.info(
            "payment captured | payment_id=%s processor_payment_id=%s amount=%d",
            record.id,
            record.processor_payment_id,
            record.amount,
        )
        return CaptureResponse(
            id=record.id,
            processor_payment_id=record.processor_payment_id,
            status=record.status,
            amount=record.amount,
            currency=record.currency,
            updated_at=record.updated_at,
        )
    except Exception:
        logger.exception(
            "capture failed, rolling back | processor_payment_id=%s",
            processor_payment_id,
        )
        await session.rollback()
        raise


async def refund(
    session: AsyncSession,
    processor_payment_id: str,
    amount: int,
    processor: PaymentProcessor,
) -> RefundResponse:
    logger.info(
        "refunding payment | processor_payment_id=%s amount=%d",
        processor_payment_id,
        amount,
    )
    await processor.refund(processor_payment_id, amount)

    try:
        record = await repository.refund_payment(session, processor_payment_id)
        if not record:
            raise PaymentNotFoundError(f"Payment not found: {processor_payment_id}")

        await session.commit()
        logger.info(
            "payment refunded | payment_id=%s processor_payment_id=%s",
            record.id,
            record.processor_payment_id,
        )
        return RefundResponse(
            id=record.id,
            processor_payment_id=record.processor_payment_id,
            status=record.status,
            amount=record.amount,
            currency=record.currency,
            updated_at=record.updated_at,
        )
    except Exception:
        logger.exception(
            "refund failed, rolling back | processor_payment_id=%s",
            processor_payment_id,
        )
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
        await issuer_settlement_service.clear_hold(
            session,
            idempotency_key=record.idempotency_key,
            amount=record.amount,
        )
        await outbox_service.publish_event(
            session,
            event_type=OutboxEventType.PAYMENT_SETTLED,
            payload={
                "payment_id": str(record.id),
                "processor_payment_id": record.processor_payment_id,
                "amount": record.amount,
                "currency": record.currency,
            },
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
        await outbox_service.publish_event(
            session,
            event_type=OutboxEventType.PAYMENT_REFUNDED,
            payload={
                "payment_id": str(record.id),
                "processor_payment_id": record.processor_payment_id,
                "amount": record.amount,
                "currency": record.currency,
            },
        )
        await session.commit()
        logger.info("Payment refunded: %s", processor_payment_id)
    except Exception:
        await session.rollback()
        raise
