import uuid
from datetime import datetime, timezone

import pytest

from app.reporting import service
from app.reporting.schemas import ReportingEventDTO, ReportingSummaryEntry

# -- helpers --


def _utc(year: int, month: int, day: int) -> datetime:
    return datetime(year, month, day, 12, 0, 0, tzinfo=timezone.utc)


# -- record_event --


async def test_record_event_persists_row(session):
    payment_id = uuid.uuid4()

    event = await service.record_event(
        session=session,
        event_type="payment.authorized",
        payment_id=payment_id,
        amount=5000,
        currency="usd",
    )

    assert isinstance(event, ReportingEventDTO)
    assert event.event_type == "payment.authorized"
    assert event.payment_id == payment_id
    assert event.amount == 5000
    assert event.currency == "usd"
    assert event.recorded_at is not None


async def test_record_event_each_lifecycle_step(session):
    payment_id = uuid.uuid4()

    for event_type in ["payment.authorized", "payment.settled", "payment.refunded"]:
        event = await service.record_event(
            session=session,
            event_type=event_type,
            payment_id=payment_id,
            amount=1000,
            currency="usd",
        )
        assert event.event_type == event_type


# -- get_summary --


async def test_summary_empty(session):
    summary = await service.get_summary(session=session)
    assert summary == []


async def test_summary_aggregates_by_date_event_type_currency(session):
    payment_id = uuid.uuid4()

    for _ in range(3):
        await service.record_event(
            session=session,
            event_type="payment.authorized",
            payment_id=payment_id,
            amount=2000,
            currency="usd",
        )

    summary = await service.get_summary(session=session)

    assert len(summary) == 1
    entry = summary[0]
    assert isinstance(entry, ReportingSummaryEntry)
    assert entry.event_type == "payment.authorized"
    assert entry.currency == "usd"
    assert entry.total_amount == 6000
    assert entry.count == 3


async def test_summary_groups_by_event_type(session):
    payment_id = uuid.uuid4()

    await service.record_event(
        session=session,
        event_type="payment.authorized",
        payment_id=payment_id,
        amount=5000,
        currency="usd",
    )
    await service.record_event(
        session=session,
        event_type="payment.settled",
        payment_id=payment_id,
        amount=5000,
        currency="usd",
    )

    summary = await service.get_summary(session=session)
    event_types = {e.event_type for e in summary}
    assert event_types == {"payment.authorized", "payment.settled"}


async def test_summary_groups_by_currency(session):
    payment_id = uuid.uuid4()

    await service.record_event(
        session=session,
        event_type="payment.authorized",
        payment_id=payment_id,
        amount=5000,
        currency="usd",
    )
    await service.record_event(
        session=session,
        event_type="payment.authorized",
        payment_id=payment_id,
        amount=4000,
        currency="eur",
    )

    summary = await service.get_summary(session=session)
    assert len(summary) == 2
    currencies = {e.currency for e in summary}
    assert currencies == {"usd", "eur"}


async def test_summary_since_filter(session):
    payment_id = uuid.uuid4()

    # two events on different days -- use recorded_at directly via repository
    from app.reporting import repository
    from app.reporting.models import ReportingEvent

    old_event = ReportingEvent(
        payment_id=payment_id,
        event_type="payment.authorized",
        amount=1000,
        currency="usd",
        recorded_at=_utc(2026, 1, 1),
    )
    new_event = ReportingEvent(
        payment_id=payment_id,
        event_type="payment.authorized",
        amount=2000,
        currency="usd",
        recorded_at=_utc(2026, 3, 1),
    )
    session.add_all([old_event, new_event])
    await session.flush()

    summary = await service.get_summary(
        session=session,
        since=_utc(2026, 2, 1),
    )

    assert len(summary) == 1
    assert summary[0].total_amount == 2000


async def test_summary_until_filter(session):
    payment_id = uuid.uuid4()

    from app.reporting.models import ReportingEvent

    old_event = ReportingEvent(
        payment_id=payment_id,
        event_type="payment.authorized",
        amount=1000,
        currency="usd",
        recorded_at=_utc(2026, 1, 1),
    )
    new_event = ReportingEvent(
        payment_id=payment_id,
        event_type="payment.authorized",
        amount=2000,
        currency="usd",
        recorded_at=_utc(2026, 3, 1),
    )
    session.add_all([old_event, new_event])
    await session.flush()

    summary = await service.get_summary(
        session=session,
        until=_utc(2026, 2, 1),
    )

    assert len(summary) == 1
    assert summary[0].total_amount == 1000


async def test_summary_since_and_until_filter(session):
    payment_id = uuid.uuid4()

    from app.reporting.models import ReportingEvent

    events = [
        ReportingEvent(
            payment_id=payment_id,
            event_type="payment.authorized",
            amount=amount,
            currency="usd",
            recorded_at=recorded_at,
        )
        for amount, recorded_at in [
            (1000, _utc(2026, 1, 1)),
            (2000, _utc(2026, 2, 15)),
            (3000, _utc(2026, 4, 1)),
        ]
    ]
    session.add_all(events)
    await session.flush()

    summary = await service.get_summary(
        session=session,
        since=_utc(2026, 2, 1),
        until=_utc(2026, 3, 1),
    )

    assert len(summary) == 1
    assert summary[0].total_amount == 2000
