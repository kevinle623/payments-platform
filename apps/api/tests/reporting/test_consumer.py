import uuid
from unittest.mock import patch

from sqlalchemy import select
from sqlalchemy.ext.asyncio import async_sessionmaker

from app.reporting.models import ReportingEvent
from workers.consumers.payments import reporting
from workers.consumers.payments.reporting import _handle

TEST_DATABASE_URL = (
    "postgresql+asyncpg://postgres:postgres@localhost:5432/payments_test"
)


def test_resolve_entity_id_prefers_payment_id():
    payment_id = uuid.uuid4()
    resolved = reporting._resolve_entity_id(
        "bill.executed",
        {
            "payment_id": str(payment_id),
            "bill_id": str(uuid.uuid4()),
        },
    )
    assert resolved == payment_id


def test_resolve_entity_id_uses_deterministic_bill_fallback():
    bill_id = uuid.uuid4()
    first = reporting._resolve_entity_id(
        "bill.failed",
        {"bill_id": str(bill_id)},
    )
    second = reporting._resolve_entity_id(
        "bill.failed",
        {"bill_id": str(bill_id)},
    )
    assert first is not None
    assert first == second


def test_resolve_entity_id_returns_none_when_missing_keys():
    resolved = reporting._resolve_entity_id("bill.failed", {})
    assert resolved is None


# -- _handle() integration tests --


async def test_handle_bill_scheduled_persists_reporting_event(engine):
    bill_id = uuid.uuid4()

    with patch("workers.consumers.payments.reporting.DATABASE_URL", TEST_DATABASE_URL):
        await _handle(
            "bill.scheduled",
            {"bill_id": str(bill_id), "amount": 3000, "currency": "usd"},
        )

    async_session = async_sessionmaker(engine, expire_on_commit=False)
    async with async_session() as session:
        result = await session.execute(
            select(ReportingEvent).where(ReportingEvent.event_type == "bill.scheduled")
        )
        row = result.scalar_one_or_none()
    assert row is not None
    assert row.amount == 3000
    assert row.currency == "usd"


async def test_handle_bill_executed_with_payment_id_uses_payment_id(engine):
    payment_id = uuid.uuid4()

    with patch("workers.consumers.payments.reporting.DATABASE_URL", TEST_DATABASE_URL):
        await _handle(
            "bill.executed",
            {"payment_id": str(payment_id), "amount": 5000, "currency": "usd"},
        )

    async_session = async_sessionmaker(engine, expire_on_commit=False)
    async with async_session() as session:
        result = await session.execute(
            select(ReportingEvent).where(ReportingEvent.event_type == "bill.executed")
        )
        row = result.scalar_one_or_none()
    assert row is not None
    assert str(row.payment_id) == str(payment_id)


async def test_handle_bill_failed_persists_reporting_event(engine):
    bill_id = uuid.uuid4()

    with patch("workers.consumers.payments.reporting.DATABASE_URL", TEST_DATABASE_URL):
        await _handle(
            "bill.failed",
            {"bill_id": str(bill_id), "amount": 2500, "currency": "eur"},
        )

    async_session = async_sessionmaker(engine, expire_on_commit=False)
    async with async_session() as session:
        result = await session.execute(
            select(ReportingEvent).where(ReportingEvent.event_type == "bill.failed")
        )
        row = result.scalar_one_or_none()
    assert row is not None
    assert row.currency == "eur"


async def test_handle_bill_executed_uses_deterministic_id_for_bill_id(engine):
    bill_id = uuid.uuid4()
    expected_id = uuid.uuid5(uuid.NAMESPACE_URL, f"bill:{bill_id}:bill.executed")

    with patch("workers.consumers.payments.reporting.DATABASE_URL", TEST_DATABASE_URL):
        await _handle(
            "bill.executed",
            {"bill_id": str(bill_id), "amount": 1000, "currency": "usd"},
        )

    async_session = async_sessionmaker(engine, expire_on_commit=False)
    async with async_session() as session:
        result = await session.execute(
            select(ReportingEvent).where(ReportingEvent.event_type == "bill.executed")
        )
        row = result.scalar_one_or_none()
    assert row is not None
    assert str(row.payment_id) == str(expected_id)


async def test_handle_skips_when_no_ids(engine):
    with patch("workers.consumers.payments.reporting.DATABASE_URL", TEST_DATABASE_URL):
        await _handle("bill.executed", {"amount": 5000, "currency": "usd"})

    async_session = async_sessionmaker(engine, expire_on_commit=False)
    async with async_session() as session:
        result = await session.execute(select(ReportingEvent))
        rows = result.scalars().all()
    assert len(rows) == 0
