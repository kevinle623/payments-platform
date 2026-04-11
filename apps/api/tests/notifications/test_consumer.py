"""
Integration tests for the notifications consumer bill event handler.

Tests _handle_bill_event() directly with a real DB session, mocking the
card/cardholder lookups and the notification sender.
"""

import uuid
from unittest.mock import AsyncMock, MagicMock, patch

from sqlalchemy import select

from app.notifications.models import NotificationLog
from workers.consumers.payments.notifications import _handle_bill_event


def _make_card(cardholder_id: uuid.UUID) -> MagicMock:
    card = MagicMock()
    card.cardholder_id = cardholder_id
    return card


def _make_cardholder(cardholder_id: uuid.UUID, email: str) -> MagicMock:
    cardholder = MagicMock()
    cardholder.id = cardholder_id
    cardholder.email = email
    return cardholder


# -- bill.executed --


async def test_handle_bill_executed_with_card_sends_and_persists(session):
    card_id = uuid.uuid4()
    cardholder_id = uuid.uuid4()
    card = _make_card(cardholder_id)
    cardholder = _make_cardholder(cardholder_id, "holder@example.com")
    mock_sender = AsyncMock()

    with (
        patch(
            "app.issuer.cards.repository.get_card",
            AsyncMock(return_value=card),
        ),
        patch(
            "app.issuer.cards.repository.get_cardholder",
            AsyncMock(return_value=cardholder),
        ),
        patch(
            "workers.consumers.payments.notifications.get_sender",
            return_value=mock_sender,
        ),
    ):
        await _handle_bill_event(
            session,
            "bill.executed",
            {"amount": 5000, "currency": "usd", "card_id": str(card_id)},
        )

    mock_sender.send.assert_awaited_once()
    _, kwargs = mock_sender.send.call_args
    assert kwargs["to_email"] == "holder@example.com"
    assert kwargs["subject"] == "Bill executed"
    assert "5000" in kwargs["body"]
    assert "USD" in kwargs["body"]

    result = await session.execute(
        select(NotificationLog).where(NotificationLog.event_type == "bill.executed")
    )
    row = result.scalar_one_or_none()
    assert row is not None
    assert str(row.cardholder_id) == str(cardholder_id)


async def test_handle_bill_scheduled_formats_next_due_date(session):
    card_id = uuid.uuid4()
    cardholder_id = uuid.uuid4()
    card = _make_card(cardholder_id)
    cardholder = _make_cardholder(cardholder_id, "holder@example.com")
    mock_sender = AsyncMock()

    with (
        patch(
            "app.issuer.cards.repository.get_card",
            AsyncMock(return_value=card),
        ),
        patch(
            "app.issuer.cards.repository.get_cardholder",
            AsyncMock(return_value=cardholder),
        ),
        patch(
            "workers.consumers.payments.notifications.get_sender",
            return_value=mock_sender,
        ),
    ):
        await _handle_bill_event(
            session,
            "bill.scheduled",
            {
                "amount": 3000,
                "currency": "usd",
                "card_id": str(card_id),
                "next_due_date": "2026-05-01",
            },
        )

    _, kwargs = mock_sender.send.call_args
    assert kwargs["subject"] == "Bill scheduled"
    assert "2026-05-01" in kwargs["body"]
    assert "3000" in kwargs["body"]


async def test_handle_bill_failed_includes_error_reason(session):
    card_id = uuid.uuid4()
    cardholder_id = uuid.uuid4()
    card = _make_card(cardholder_id)
    cardholder = _make_cardholder(cardholder_id, "holder@example.com")
    mock_sender = AsyncMock()

    with (
        patch(
            "app.issuer.cards.repository.get_card",
            AsyncMock(return_value=card),
        ),
        patch(
            "app.issuer.cards.repository.get_cardholder",
            AsyncMock(return_value=cardholder),
        ),
        patch(
            "workers.consumers.payments.notifications.get_sender",
            return_value=mock_sender,
        ),
    ):
        await _handle_bill_event(
            session,
            "bill.failed",
            {
                "amount": 2000,
                "currency": "usd",
                "card_id": str(card_id),
                "error": "Insufficient funds",
            },
        )

    _, kwargs = mock_sender.send.call_args
    assert kwargs["subject"] == "Bill failed"
    assert "Insufficient funds" in kwargs["body"]


# -- no card_id --


async def test_handle_bill_event_without_card_id_persists_log_no_email(session):
    mock_sender = AsyncMock()

    with patch(
        "workers.consumers.payments.notifications.get_sender",
        return_value=mock_sender,
    ):
        await _handle_bill_event(
            session,
            "bill.executed",
            {"amount": 5000, "currency": "usd"},
        )

    mock_sender.send.assert_not_awaited()

    result = await session.execute(
        select(NotificationLog).where(NotificationLog.event_type == "bill.executed")
    )
    row = result.scalar_one_or_none()
    assert row is not None
    assert row.cardholder_id is None


# -- card not found --


async def test_handle_bill_event_card_not_found_persists_log_no_email(session):
    card_id = uuid.uuid4()
    mock_sender = AsyncMock()

    with (
        patch(
            "app.issuer.cards.repository.get_card",
            AsyncMock(return_value=None),
        ),
        patch(
            "workers.consumers.payments.notifications.get_sender",
            return_value=mock_sender,
        ),
    ):
        await _handle_bill_event(
            session,
            "bill.executed",
            {"amount": 5000, "currency": "usd", "card_id": str(card_id)},
        )

    mock_sender.send.assert_not_awaited()

    result = await session.execute(
        select(NotificationLog).where(NotificationLog.event_type == "bill.executed")
    )
    row = result.scalar_one_or_none()
    assert row is not None
    assert row.cardholder_id is None


# -- cardholder not found --


async def test_handle_bill_event_cardholder_not_found_persists_log_no_email(session):
    card_id = uuid.uuid4()
    cardholder_id = uuid.uuid4()
    card = _make_card(cardholder_id)
    mock_sender = AsyncMock()

    with (
        patch(
            "app.issuer.cards.repository.get_card",
            AsyncMock(return_value=card),
        ),
        patch(
            "app.issuer.cards.repository.get_cardholder",
            AsyncMock(return_value=None),
        ),
        patch(
            "workers.consumers.payments.notifications.get_sender",
            return_value=mock_sender,
        ),
    ):
        await _handle_bill_event(
            session,
            "bill.executed",
            {"amount": 5000, "currency": "usd", "card_id": str(card_id)},
        )

    mock_sender.send.assert_not_awaited()

    result = await session.execute(
        select(NotificationLog).where(NotificationLog.event_type == "bill.executed")
    )
    row = result.scalar_one_or_none()
    assert row is not None
    assert row.cardholder_id is None
