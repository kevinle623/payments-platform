from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.payments.models import Payment
from app.payments.schemas import AuthorizeResponse, PaymentRecord
from shared.processors.base import PaymentStatus


async def _get_orm_by_processor_payment_id(
    session: AsyncSession,
    processor_payment_id: str,
) -> Payment | None:
    result = await session.execute(
        select(Payment).where(Payment.processor_payment_id == processor_payment_id)
    )
    return result.scalar_one_or_none()


async def _get_orm_by_idempotency_key(
    session: AsyncSession,
    idempotency_key: str,
) -> Payment | None:
    result = await session.execute(
        select(Payment).where(Payment.idempotency_key == idempotency_key)
    )
    return result.scalar_one_or_none()


async def _update_processor_payment_id(
    session: AsyncSession,
    payment: Payment,
    processor_payment_id: str,
) -> Payment:
    payment.processor_payment_id = processor_payment_id
    await session.flush()
    return payment


async def _update_status(
    session: AsyncSession,
    payment: Payment,
    status: PaymentStatus,
) -> Payment:
    payment.status = status
    await session.flush()
    return payment


# public functions -- only these are called from outside the repository


async def get_by_idempotency_key(
    session: AsyncSession,
    idempotency_key: str,
) -> AuthorizeResponse | None:
    orm_object = await _get_orm_by_idempotency_key(session, idempotency_key)
    if orm_object is None:
        return None
    return AuthorizeResponse.model_validate(orm_object)


async def create(
    session: AsyncSession,
    idempotency_key: str,
    amount: int,
    currency: str,
    processor: str,
    processor_payment_id: str,
) -> PaymentRecord:
    payment = Payment(
        idempotency_key=idempotency_key,
        amount=amount,
        currency=currency,
        processor=processor,
        status=PaymentStatus.PENDING,
    )
    session.add(payment)
    await session.flush()
    updated = await _update_processor_payment_id(session, payment, processor_payment_id)
    return PaymentRecord.model_validate(updated)


async def settle(
    session: AsyncSession,
    processor_payment_id: str,
) -> PaymentRecord | None:
    payment = await _get_orm_by_processor_payment_id(session, processor_payment_id)
    if payment is None:
        return None
    updated = await _update_status(session, payment, PaymentStatus.SUCCEEDED)
    return PaymentRecord.model_validate(updated)


async def fail(
    session: AsyncSession,
    processor_payment_id: str,
) -> PaymentRecord | None:
    payment = await _get_orm_by_processor_payment_id(session, processor_payment_id)
    if payment is None:
        return None
    updated = await _update_status(session, payment, PaymentStatus.FAILED)
    return PaymentRecord.model_validate(updated)


async def refund_payment(
    session: AsyncSession,
    processor_payment_id: str,
) -> PaymentRecord | None:
    payment = await _get_orm_by_processor_payment_id(session, processor_payment_id)
    if payment is None:
        return None
    updated = await _update_status(session, payment, PaymentStatus.REFUNDED)
    return PaymentRecord.model_validate(updated)
