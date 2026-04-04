import uuid

import pytest
from sqlalchemy import select

from app.fraud import service
from app.fraud.models import FraudSignal, RiskLevel
from app.fraud.schemas import FraudSignalDTO


async def test_create_signal_persists_row(session):
    payment_id = uuid.uuid4()

    signal = await service.create_signal(
        session=session,
        payment_id=payment_id,
        risk_level=RiskLevel.HIGH,
        amount=15000,
        currency="usd",
    )

    assert isinstance(signal, FraudSignalDTO)
    assert signal.payment_id == payment_id
    assert signal.risk_level == RiskLevel.HIGH
    assert signal.amount == 15000
    assert signal.currency == "usd"
    assert signal.flagged_at is not None

    result = await session.execute(
        select(FraudSignal).where(FraudSignal.id == signal.id)
    )
    row = result.scalar_one_or_none()
    assert row is not None
    assert str(row.payment_id) == str(payment_id)


async def test_create_low_risk_signal(session):
    payment_id = uuid.uuid4()

    signal = await service.create_signal(
        session=session,
        payment_id=payment_id,
        risk_level=RiskLevel.LOW,
        amount=500,
        currency="usd",
    )

    assert signal.risk_level == RiskLevel.LOW
    assert signal.amount == 500


async def test_list_signals_empty(session):
    signals = await service.list_signals(session=session)
    assert signals == []


async def test_list_signals_returns_all(session):
    payment_a = uuid.uuid4()
    payment_b = uuid.uuid4()

    await service.create_signal(
        session=session,
        payment_id=payment_a,
        risk_level=RiskLevel.LOW,
        amount=1000,
        currency="usd",
    )
    await service.create_signal(
        session=session,
        payment_id=payment_b,
        risk_level=RiskLevel.HIGH,
        amount=20000,
        currency="usd",
    )

    signals = await service.list_signals(session=session)
    assert len(signals) == 2


async def test_list_signals_filter_by_risk_level(session):
    await service.create_signal(
        session=session,
        payment_id=uuid.uuid4(),
        risk_level=RiskLevel.LOW,
        amount=500,
        currency="usd",
    )
    await service.create_signal(
        session=session,
        payment_id=uuid.uuid4(),
        risk_level=RiskLevel.HIGH,
        amount=25000,
        currency="usd",
    )
    await service.create_signal(
        session=session,
        payment_id=uuid.uuid4(),
        risk_level=RiskLevel.HIGH,
        amount=50000,
        currency="usd",
    )

    high_signals = await service.list_signals(
        session=session, risk_level=RiskLevel.HIGH
    )
    assert len(high_signals) == 2
    assert all(s.risk_level == RiskLevel.HIGH for s in high_signals)

    low_signals = await service.list_signals(session=session, risk_level=RiskLevel.LOW)
    assert len(low_signals) == 1
    assert low_signals[0].risk_level == RiskLevel.LOW


async def test_list_signals_pagination(session):
    for i in range(5):
        await service.create_signal(
            session=session,
            payment_id=uuid.uuid4(),
            risk_level=RiskLevel.LOW,
            amount=100 * (i + 1),
            currency="usd",
        )

    page1 = await service.list_signals(session=session, limit=3, offset=0)
    page2 = await service.list_signals(session=session, limit=3, offset=3)

    assert len(page1) == 3
    assert len(page2) == 2
    # no overlap
    page1_ids = {s.id for s in page1}
    page2_ids = {s.id for s in page2}
    assert page1_ids.isdisjoint(page2_ids)


async def test_list_signals_ordered_by_flagged_at_desc(session):
    for amount in [1000, 2000, 3000]:
        await service.create_signal(
            session=session,
            payment_id=uuid.uuid4(),
            risk_level=RiskLevel.LOW,
            amount=amount,
            currency="usd",
        )

    signals = await service.list_signals(session=session)
    timestamps = [s.flagged_at for s in signals]
    assert timestamps == sorted(timestamps, reverse=True)
