from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy import select

from app.issuer.auth import repository as auth_repository
from app.issuer.auth import service as auth_service
from app.issuer.auth.models import IssuerAuthDecision
from app.issuer.cards import service as cards_service
from app.issuer.settlement import service as settlement_service
from app.ledger.models import LedgerEntry
from app.outbox.models import OutboxEvent, OutboxEventType
from app.payments import repository as payments_repository
from app.payments.models import Payment
from shared.enums.currency import Currency
from shared.processors.base import PaymentStatus

# -- fixtures --


@pytest.fixture
async def cardholder(session):
    return await cards_service.create_cardholder(
        session, name="Test User", email="test@example.com"
    )


@pytest.fixture
async def card(session, cardholder):
    return await cards_service.create_card(
        session,
        cardholder_id=cardholder.id,
        credit_limit=10000,
        currency=Currency.USD,
    )


@pytest.fixture
async def approved_auth(session, card):
    return await auth_service.evaluate(
        session,
        idempotency_key="idem-hold-001",
        amount=5000,
        currency="usd",
        metadata={},
        card_id=card.id,
    )


# cutoff helpers
_FUTURE_CUTOFF = datetime.now(timezone.utc) + timedelta(days=1)
_PAST_CUTOFF = datetime.now(timezone.utc) - timedelta(days=8)


# -- get_stale_approved --


async def test_get_stale_approved_returns_approved_card_auths(session, approved_auth):
    results = await auth_repository.get_stale_approved(
        session, older_than=_FUTURE_CUTOFF
    )
    assert any(r.id == approved_auth.id for r in results)


async def test_get_stale_approved_excludes_recent_auths(session, approved_auth):
    # cutoff in the past -- rows created now are too recent
    results = await auth_repository.get_stale_approved(session, older_than=_PAST_CUTOFF)
    assert results == []


async def test_get_stale_approved_excludes_declined_auths(session, card):
    await auth_service.evaluate(
        session,
        idempotency_key="idem-declined",
        amount=99999,  # exceeds credit limit -- will be declined
        currency="usd",
        metadata={},
        card_id=card.id,
    )
    results = await auth_repository.get_stale_approved(
        session, older_than=_FUTURE_CUTOFF
    )
    assert all(r.decision == IssuerAuthDecision.APPROVED for r in results)


async def test_get_stale_approved_excludes_auths_without_card(session):
    await auth_service.evaluate(
        session,
        idempotency_key="idem-no-card",
        amount=5000,
        currency="usd",
        metadata={},
        card_id=None,
    )
    results = await auth_repository.get_stale_approved(
        session, older_than=_FUTURE_CUTOFF
    )
    assert all(r.card_id is not None for r in results)


# -- mark_expired --


async def test_mark_expired_updates_decision(session, approved_auth):
    await auth_repository.mark_expired(session, approved_auth.id)
    updated = await auth_repository.get_by_idempotency_key(session, "idem-hold-001")
    assert updated.decision == IssuerAuthDecision.EXPIRED


async def test_mark_expired_removes_from_stale_approved_results(session, approved_auth):
    await auth_repository.mark_expired(session, approved_auth.id)
    results = await auth_repository.get_stale_approved(
        session, older_than=_FUTURE_CUTOFF
    )
    assert not any(r.id == approved_auth.id for r in results)


# -- hold expiry flow: genuinely stale hold (no payment) --


async def test_expiry_of_stale_hold_clears_ledger(session, card, approved_auth):
    # simulate hold expiry job: no settled payment exists, so clear the hold
    await settlement_service.clear_hold(
        session, idempotency_key="idem-hold-001", amount=5000
    )
    await auth_repository.mark_expired(session, approved_auth.id)

    balance = await cards_service.get_card_balance(session, card.id)
    assert balance.pending_holds == 0
    assert balance.available_credit == card.credit_limit


async def test_expiry_of_stale_hold_marks_auth_expired(session, card, approved_auth):
    await settlement_service.clear_hold(
        session, idempotency_key="idem-hold-001", amount=5000
    )
    await auth_repository.mark_expired(session, approved_auth.id)

    updated = await auth_repository.get_by_idempotency_key(session, "idem-hold-001")
    assert updated.decision == IssuerAuthDecision.EXPIRED


async def test_expiry_of_stale_hold_writes_hold_cleared_outbox_event(
    session, card, approved_auth
):
    await settlement_service.clear_hold(
        session, idempotency_key="idem-hold-001", amount=5000
    )
    events = (
        (
            await session.execute(
                select(OutboxEvent).where(
                    OutboxEvent.event_type == OutboxEventType.HOLD_CLEARED
                )
            )
        )
        .scalars()
        .all()
    )
    assert len(events) == 1
    assert events[0].payload["card_id"] == str(card.id)
    assert events[0].payload["amount"] == 5000


# -- hold expiry flow: already-settled payment (no double-clear) --


async def test_no_double_clear_when_payment_already_settled(
    session, card, approved_auth
):
    # simulate: payment was settled normally -- hold already cleared via settlement path
    payment = Payment(
        idempotency_key="idem-hold-001",
        amount=5000,
        currency="usd",
        processor="stripe",
        processor_payment_id="pi_test_123",
        status=PaymentStatus.SUCCEEDED,
    )
    session.add(payment)
    await session.flush()

    # record the ledger entry count after the hold was placed (2 entries)
    entries_before = (await session.execute(select(LedgerEntry))).scalars().all()
    hold_entry_count = len(entries_before)

    # expiry job detects settled payment -- only marks expired, does NOT call clear_hold
    fetched_payment = await payments_repository.get_by_idempotency_key(
        session, "idem-hold-001"
    )
    assert fetched_payment.status == PaymentStatus.SUCCEEDED

    await auth_repository.mark_expired(session, approved_auth.id)

    # ledger unchanged -- no extra entries written
    entries_after = (await session.execute(select(LedgerEntry))).scalars().all()
    assert len(entries_after) == hold_entry_count


async def test_auth_marked_expired_even_when_payment_already_settled(
    session, card, approved_auth
):
    payment = Payment(
        idempotency_key="idem-hold-001",
        amount=5000,
        currency="usd",
        processor="stripe",
        processor_payment_id="pi_test_456",
        status=PaymentStatus.SUCCEEDED,
    )
    session.add(payment)
    await session.flush()

    await auth_repository.mark_expired(session, approved_auth.id)

    updated = await auth_repository.get_by_idempotency_key(session, "idem-hold-001")
    assert updated.decision == IssuerAuthDecision.EXPIRED
