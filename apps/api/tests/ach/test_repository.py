"""
Integration tests for get_pending_ach() repository function.
"""

import uuid

from app.payments import repository as payments_repository
from shared.processors.base import PaymentStatus


async def test_get_pending_ach_returns_only_pending_ach_payments(session):
    ach_payment = await payments_repository.create(
        session=session,
        idempotency_key="ach-pending-001",
        amount=5000,
        currency="usd",
        processor="ach",
        processor_payment_id=f"ach_{uuid.uuid4().hex}",
    )
    # pending Stripe -- should be excluded
    await payments_repository.create(
        session=session,
        idempotency_key="stripe-pending-001",
        amount=3000,
        currency="usd",
        processor="stripe",
        processor_payment_id="pi_test_excluded",
    )

    results = await payments_repository.get_pending_ach(session)

    assert len(results) == 1
    assert str(results[0].id) == str(ach_payment.id)


async def test_get_pending_ach_excludes_settled_ach_payments(session):
    payment = await payments_repository.create(
        session=session,
        idempotency_key="ach-settled-001",
        amount=5000,
        currency="usd",
        processor="ach",
        processor_payment_id=f"ach_{uuid.uuid4().hex}",
    )
    await payments_repository.settle(session, payment.processor_payment_id)

    results = await payments_repository.get_pending_ach(session)

    assert results == []


async def test_get_pending_ach_excludes_failed_ach_payments(session):
    payment = await payments_repository.create(
        session=session,
        idempotency_key="ach-failed-001",
        amount=5000,
        currency="usd",
        processor="ach",
        processor_payment_id=f"ach_{uuid.uuid4().hex}",
    )
    await payments_repository.fail(session, payment.processor_payment_id)

    results = await payments_repository.get_pending_ach(session)

    assert results == []


async def test_get_pending_ach_returns_multiple(session):
    for i in range(3):
        await payments_repository.create(
            session=session,
            idempotency_key=f"ach-multi-{i:03d}",
            amount=1000 * (i + 1),
            currency="usd",
            processor="ach",
            processor_payment_id=f"ach_{uuid.uuid4().hex}",
        )

    results = await payments_repository.get_pending_ach(session)

    assert len(results) == 3
    assert all(r.status == PaymentStatus.PENDING for r in results)


async def test_get_pending_ach_returns_empty_when_none(session):
    results = await payments_repository.get_pending_ach(session)

    assert results == []
