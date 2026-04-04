import uuid
from unittest.mock import AsyncMock

import pytest
from sqlalchemy import select

from app.notifications import service
from app.notifications.models import NotificationChannel, NotificationLog
from app.notifications.schemas import NotificationLogDTO
from app.notifications.sender.adapters.stub import StubSender

# -- fixtures --


@pytest.fixture
def stub_sender():
    """Real StubSender -- just logs, no network."""
    return StubSender()


@pytest.fixture
def mock_sender():
    """AsyncMock so we can assert send() was called with the right args."""
    sender = AsyncMock()
    sender.send = AsyncMock()
    return sender


# -- tests: log persistence --


async def test_send_and_log_persists_row(session, stub_sender):
    log = await service.send_and_log(
        session=session,
        sender=stub_sender,
        event_type="payment.authorized",
        message="Your payment of 5000 USD has been authorized.",
    )

    assert isinstance(log, NotificationLogDTO)
    assert log.event_type == "payment.authorized"
    assert log.channel == NotificationChannel.EMAIL
    assert log.cardholder_id is None
    assert log.sent_at is not None

    result = await session.execute(
        select(NotificationLog).where(NotificationLog.id == log.id)
    )
    row = result.scalar_one_or_none()
    assert row is not None
    assert row.message == "Your payment of 5000 USD has been authorized."


async def test_send_and_log_persists_cardholder_id(session, stub_sender):
    cardholder_id = uuid.uuid4()

    log = await service.send_and_log(
        session=session,
        sender=stub_sender,
        event_type="payment.settled",
        message="Your payment of 2000 USD has been completed.",
        cardholder_id=cardholder_id,
    )

    assert log.cardholder_id == cardholder_id

    result = await session.execute(
        select(NotificationLog).where(NotificationLog.id == log.id)
    )
    row = result.scalar_one_or_none()
    assert str(row.cardholder_id) == str(cardholder_id)


# -- tests: mock delivery --


async def test_send_and_log_calls_sender_when_email_provided(session, mock_sender):
    await service.send_and_log(
        session=session,
        sender=mock_sender,
        event_type="payment.authorized",
        message="Your payment has been authorized.",
        to_email="cardholder@example.com",
    )

    mock_sender.send.assert_awaited_once_with(
        to_email="cardholder@example.com",
        subject="Payment authorized",
        body="Your payment has been authorized.",
    )


async def test_send_and_log_skips_sender_when_no_email(session, mock_sender):
    await service.send_and_log(
        session=session,
        sender=mock_sender,
        event_type="payment.authorized",
        message="Your payment has been authorized.",
        to_email=None,
    )

    mock_sender.send.assert_not_awaited()


async def test_send_and_log_still_persists_when_no_email(session, mock_sender):
    log = await service.send_and_log(
        session=session,
        sender=mock_sender,
        event_type="payment.refunded",
        message="Your refund is being processed.",
        to_email=None,
    )

    assert log.id is not None
    assert log.event_type == "payment.refunded"


# -- tests: subject mapping --


async def test_subjects_for_known_event_types(session, mock_sender):
    event_types = [
        ("payment.authorized", "Payment authorized"),
        ("payment.settled", "Payment completed"),
        ("payment.refunded", "Refund processed"),
    ]
    for event_type, expected_subject in event_types:
        await service.send_and_log(
            session=session,
            sender=mock_sender,
            event_type=event_type,
            message="msg",
            to_email="test@example.com",
        )
        _, kwargs = mock_sender.send.call_args
        assert kwargs["subject"] == expected_subject
        mock_sender.send.reset_mock()


async def test_subject_fallback_for_unknown_event_type(session, mock_sender):
    await service.send_and_log(
        session=session,
        sender=mock_sender,
        event_type="payment.unknown",
        message="msg",
        to_email="test@example.com",
    )

    _, kwargs = mock_sender.send.call_args
    assert kwargs["subject"] == "Payment notification"


# -- tests: multiple logs --


async def test_multiple_events_create_separate_log_rows(session, stub_sender):
    for event_type in ["payment.authorized", "payment.settled", "payment.refunded"]:
        await service.send_and_log(
            session=session,
            sender=stub_sender,
            event_type=event_type,
            message=f"msg for {event_type}",
        )

    result = await session.execute(select(NotificationLog))
    rows = result.scalars().all()
    assert len(rows) == 3
    assert {r.event_type for r in rows} == {
        "payment.authorized",
        "payment.settled",
        "payment.refunded",
    }
