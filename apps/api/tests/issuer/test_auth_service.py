import uuid

import pytest
from sqlalchemy import select

from app.issuer.auth import service as auth_service
from app.issuer.auth.models import IssuerAuthDecision
from app.issuer.cards import service as cards_service
from app.issuer.cards.models import Card, CardStatus
from app.issuer.controls import service as controls_service
from app.ledger.models import LedgerEntry
from app.outbox.models import OutboxEvent, OutboxEventType
from shared.enums.currency import Currency

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
        credit_limit=10000,  # $100
        currency=Currency.USD,
    )


# -- no card_id path --


async def test_evaluate_without_card_approves(session):
    result = await auth_service.evaluate(
        session,
        idempotency_key="idem-001",
        amount=5000,
        currency="usd",
        metadata={},
        card_id=None,
    )
    assert result.decision == IssuerAuthDecision.APPROVED
    assert result.card_id is None


async def test_evaluate_without_card_writes_no_ledger_entries(session):
    await auth_service.evaluate(
        session,
        idempotency_key="idem-001",
        amount=5000,
        currency="usd",
        metadata={},
        card_id=None,
    )
    entries = (await session.execute(select(LedgerEntry))).scalars().all()
    assert entries == []


# -- approved path with card --


async def test_evaluate_with_card_approves_and_places_hold(session, card):
    result = await auth_service.evaluate(
        session,
        idempotency_key="idem-001",
        amount=5000,
        currency="usd",
        metadata={},
        card_id=card.id,
    )
    assert result.decision == IssuerAuthDecision.APPROVED
    assert result.card_id == card.id

    entries = (await session.execute(select(LedgerEntry))).scalars().all()
    amounts = {e.account_id: e.amount for e in entries}
    assert amounts[card.available_balance_account_id] == -5000
    assert amounts[card.pending_hold_account_id] == 5000


# -- declined paths --


async def test_evaluate_declines_card_not_found(session):
    result = await auth_service.evaluate(
        session,
        idempotency_key="idem-001",
        amount=5000,
        currency="usd",
        metadata={},
        card_id=uuid.uuid4(),
    )
    assert result.decision == IssuerAuthDecision.DECLINED
    assert result.decline_reason == "card_not_found"


async def test_evaluate_declines_inactive_card(session, card):
    orm_card = (
        await session.execute(select(Card).where(Card.id == card.id))
    ).scalar_one()
    orm_card.status = CardStatus.FROZEN
    await session.flush()

    result = await auth_service.evaluate(
        session,
        idempotency_key="idem-001",
        amount=5000,
        currency="usd",
        metadata={},
        card_id=card.id,
    )
    assert result.decision == IssuerAuthDecision.DECLINED
    assert result.decline_reason == "card_inactive"


async def test_evaluate_declines_insufficient_funds(session, card):
    result = await auth_service.evaluate(
        session,
        idempotency_key="idem-001",
        amount=20000,  # $200 > $100 credit limit
        currency="usd",
        metadata={},
        card_id=card.id,
    )
    assert result.decision == IssuerAuthDecision.DECLINED
    assert result.decline_reason == "insufficient_funds"


async def test_evaluate_declined_writes_no_ledger_entries(session, card):
    await auth_service.evaluate(
        session,
        idempotency_key="idem-001",
        amount=20000,
        currency="usd",
        metadata={},
        card_id=card.id,
    )
    entries = (await session.execute(select(LedgerEntry))).scalars().all()
    assert entries == []


async def test_evaluate_declines_mcc_blocked(session, card):
    await controls_service.add_mcc_block(session, card_id=card.id, mcc="7995")

    result = await auth_service.evaluate(
        session,
        idempotency_key="idem-001",
        amount=1000,
        currency="usd",
        metadata={"mcc": "7995"},
        card_id=card.id,
    )
    assert result.decision == IssuerAuthDecision.DECLINED
    assert result.decline_reason == "mcc_blocked"


async def test_evaluate_unblocked_mcc_passes(session, card):
    await controls_service.add_mcc_block(session, card_id=card.id, mcc="7995")

    result = await auth_service.evaluate(
        session,
        idempotency_key="idem-001",
        amount=1000,
        currency="usd",
        metadata={"mcc": "5411"},  # groceries -- not blocked
        card_id=card.id,
    )
    assert result.decision == IssuerAuthDecision.APPROVED


async def test_evaluate_declines_velocity_exceeded(session, cardholder):
    # use a high credit limit so balance check does not interfere
    high_limit_card = await cards_service.create_card(
        session,
        cardholder_id=cardholder.id,
        credit_limit=100000,  # $1000
        currency=Currency.USD,
    )
    await controls_service.add_velocity_rule(
        session,
        card_id=high_limit_card.id,
        max_amount=10000,  # $100/day
        window_seconds=86400,
    )

    # first auth: $60 -- passes
    await auth_service.evaluate(
        session,
        idempotency_key="idem-001",
        amount=6000,
        currency="usd",
        metadata={},
        card_id=high_limit_card.id,
    )

    # second auth: $60 -- fails velocity ($60 + $60 = $120 > $100)
    result = await auth_service.evaluate(
        session,
        idempotency_key="idem-002",
        amount=6000,
        currency="usd",
        metadata={},
        card_id=high_limit_card.id,
    )
    assert result.decision == IssuerAuthDecision.DECLINED
    assert result.decline_reason == "velocity_exceeded"


# -- idempotency --


async def test_evaluate_idempotency_returns_existing_record(session, card):
    first = await auth_service.evaluate(
        session,
        idempotency_key="idem-001",
        amount=5000,
        currency="usd",
        metadata={},
        card_id=card.id,
    )
    second = await auth_service.evaluate(
        session,
        idempotency_key="idem-001",
        amount=5000,
        currency="usd",
        metadata={},
        card_id=card.id,
    )
    assert first.id == second.id
    assert first.decision == second.decision


async def test_evaluate_idempotency_does_not_double_write_hold(session, card):
    await auth_service.evaluate(
        session,
        idempotency_key="idem-001",
        amount=5000,
        currency="usd",
        metadata={},
        card_id=card.id,
    )
    await auth_service.evaluate(
        session,
        idempotency_key="idem-001",
        amount=5000,
        currency="usd",
        metadata={},
        card_id=card.id,
    )
    # still only 2 entries -- hold was not written twice
    entries = (await session.execute(select(LedgerEntry))).scalars().all()
    assert len(entries) == 2


# -- ledger invariants --


async def test_ledger_invariant_hold_entries_sum_to_zero(session, card):
    await auth_service.evaluate(
        session,
        idempotency_key="idem-001",
        amount=5000,
        currency="usd",
        metadata={},
        card_id=card.id,
    )
    entries = (await session.execute(select(LedgerEntry))).scalars().all()
    assert sum(e.amount for e in entries) == 0


async def test_available_credit_reduces_after_hold(session, card):
    await auth_service.evaluate(
        session,
        idempotency_key="idem-001",
        amount=5000,
        currency="usd",
        metadata={},
        card_id=card.id,
    )
    balance = await cards_service.get_card_balance(session, card.id)
    assert balance.available_credit == 5000  # $100 - $50 = $50
    assert balance.pending_holds == 5000


# -- outbox events --


async def test_evaluate_approved_writes_auth_approved_outbox_event(session, card):
    await auth_service.evaluate(
        session,
        idempotency_key="idem-001",
        amount=5000,
        currency="usd",
        metadata={},
        card_id=card.id,
    )
    events = (
        (
            await session.execute(
                select(OutboxEvent).where(
                    OutboxEvent.event_type == OutboxEventType.AUTH_APPROVED
                )
            )
        )
        .scalars()
        .all()
    )
    assert len(events) == 1
    assert events[0].payload["card_id"] == str(card.id)
    assert events[0].payload["amount"] == 5000


async def test_evaluate_declined_writes_auth_declined_outbox_event(session, card):
    await auth_service.evaluate(
        session,
        idempotency_key="idem-001",
        amount=99999,  # exceeds credit limit
        currency="usd",
        metadata={},
        card_id=card.id,
    )
    events = (
        (
            await session.execute(
                select(OutboxEvent).where(
                    OutboxEvent.event_type == OutboxEventType.AUTH_DECLINED
                )
            )
        )
        .scalars()
        .all()
    )
    assert len(events) == 1
    assert events[0].payload["decline_reason"] == "insufficient_funds"


async def test_evaluate_approved_writes_hold_created_outbox_event(session, card):
    await auth_service.evaluate(
        session,
        idempotency_key="idem-001",
        amount=5000,
        currency="usd",
        metadata={},
        card_id=card.id,
    )
    events = (
        (
            await session.execute(
                select(OutboxEvent).where(
                    OutboxEvent.event_type == OutboxEventType.HOLD_CREATED
                )
            )
        )
        .scalars()
        .all()
    )
    assert len(events) == 1
    assert events[0].payload["amount"] == 5000


async def test_evaluate_idempotency_does_not_double_write_outbox_events(session, card):
    for _ in range(2):
        await auth_service.evaluate(
            session,
            idempotency_key="idem-001",
            amount=5000,
            currency="usd",
            metadata={},
            card_id=card.id,
        )
    approved_events = (
        (
            await session.execute(
                select(OutboxEvent).where(
                    OutboxEvent.event_type == OutboxEventType.AUTH_APPROVED
                )
            )
        )
        .scalars()
        .all()
    )
    assert len(approved_events) == 1
