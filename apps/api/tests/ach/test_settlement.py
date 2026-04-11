"""
Integration tests for the ACH settlement job (_run).

_run() creates its own engine, so we patch DATABASE_URL to point at the test
DB and seed data via the shared engine fixture (which owns table lifecycle).
Seeded payments are committed so _run()'s sessions can see them.
"""

import uuid
from unittest.mock import patch

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import async_sessionmaker

from app.ledger.models import LedgerAccount
from app.payments import repository as payments_repository
from app.payments.models import Payment
from shared.enums.currency import Currency
from shared.processors.base import PaymentStatus
from shared.settings import CASH_ACCOUNT_ID, LIABILITY_ACCOUNT_ID
from workers.jobs.payments.ach_settlement import _run

TEST_DATABASE_URL = (
    "postgresql+asyncpg://postgres:postgres@localhost:5432/payments_test"
)


@pytest.fixture
async def ledger_accounts(session):
    """Seed the fixed-UUID ledger accounts required by handle_payment_succeeded."""
    liability = LedgerAccount(
        id=uuid.UUID(LIABILITY_ACCOUNT_ID),
        name="liability",
        account_type="liability",
        currency=Currency.USD,
    )
    cash = LedgerAccount(
        id=uuid.UUID(CASH_ACCOUNT_ID),
        name="cash",
        account_type="asset",
        currency=Currency.USD,
    )
    session.add_all([liability, cash])
    await session.flush()
    return liability, cash


async def test_run_settles_pending_ach_payment(session, engine, ledger_accounts):
    processor_payment_id = f"ach_{uuid.uuid4().hex}"
    await payments_repository.create(
        session=session,
        idempotency_key="ach-settle-job-001",
        amount=5000,
        currency="usd",
        processor="ach",
        processor_payment_id=processor_payment_id,
    )
    await session.commit()

    with patch("workers.jobs.payments.ach_settlement.DATABASE_URL", TEST_DATABASE_URL):
        await _run()

    async_session = async_sessionmaker(engine, expire_on_commit=False)
    async with async_session() as s:
        result = await s.execute(
            select(Payment).where(Payment.processor_payment_id == processor_payment_id)
        )
        payment = result.scalar_one()
    assert payment.status == PaymentStatus.SUCCEEDED


async def test_run_settles_multiple_pending_ach_payments(
    session, engine, ledger_accounts
):
    processor_ids = [f"ach_{uuid.uuid4().hex}" for _ in range(3)]
    for i, pid in enumerate(processor_ids):
        await payments_repository.create(
            session=session,
            idempotency_key=f"ach-settle-multi-{i:03d}",
            amount=1000 * (i + 1),
            currency="usd",
            processor="ach",
            processor_payment_id=pid,
        )
    await session.commit()

    with patch("workers.jobs.payments.ach_settlement.DATABASE_URL", TEST_DATABASE_URL):
        await _run()

    async_session = async_sessionmaker(engine, expire_on_commit=False)
    async with async_session() as s:
        result = await s.execute(select(Payment).where(Payment.processor == "ach"))
        payments = result.scalars().all()
    assert all(p.status == PaymentStatus.SUCCEEDED for p in payments)


async def test_run_does_not_settle_stripe_pending_payments(
    session, engine, ledger_accounts
):
    await payments_repository.create(
        session=session,
        idempotency_key="stripe-not-settled-001",
        amount=5000,
        currency="usd",
        processor="stripe",
        processor_payment_id="pi_test_stripe_skip",
    )
    await session.commit()

    with patch("workers.jobs.payments.ach_settlement.DATABASE_URL", TEST_DATABASE_URL):
        await _run()

    async_session = async_sessionmaker(engine, expire_on_commit=False)
    async with async_session() as s:
        result = await s.execute(
            select(Payment).where(Payment.processor_payment_id == "pi_test_stripe_skip")
        )
        payment = result.scalar_one()
    assert payment.status == PaymentStatus.PENDING


async def test_run_is_noop_when_no_pending_ach(engine):
    # tables exist but no data -- should complete without error
    with patch("workers.jobs.payments.ach_settlement.DATABASE_URL", TEST_DATABASE_URL):
        await _run()
