import pytest
from sqlalchemy import select

from app.issuer.auth import repository as auth_repository
from app.issuer.auth import service as auth_service
from app.issuer.auth.models import IssuerAuthDecision
from app.issuer.cards import service as cards_service
from app.issuer.settlement import service as settlement_service
from app.ledger.models import LedgerEntry
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
        credit_limit=10000,
        currency=Currency.USD,
    )


@pytest.fixture
async def approved_auth(session, card):
    return await auth_service.evaluate(
        session,
        idempotency_key="idem-001",
        amount=5000,
        currency="usd",
        metadata={},
        card_id=card.id,
    )


# -- clear_hold happy path --


async def test_clear_hold_writes_ledger_entries(session, card, approved_auth):
    await settlement_service.clear_hold(
        session, idempotency_key="idem-001", amount=5000
    )
    entries = (await session.execute(select(LedgerEntry))).scalars().all()
    # 2 from hold + 2 from clear
    assert len(entries) == 4


async def test_clear_hold_reverses_pending_hold(session, card, approved_auth):
    await settlement_service.clear_hold(
        session, idempotency_key="idem-001", amount=5000
    )
    balance = await cards_service.get_card_balance(session, card.id)
    assert balance.pending_holds == 0


async def test_clear_hold_restores_available_credit(session, card, approved_auth):
    await settlement_service.clear_hold(
        session, idempotency_key="idem-001", amount=5000
    )
    balance = await cards_service.get_card_balance(session, card.id)
    assert balance.available_credit == card.credit_limit


# -- skip paths --


async def test_clear_hold_skips_when_no_issuer_auth(session):
    # should not raise, no entries written
    await settlement_service.clear_hold(
        session, idempotency_key="nonexistent-key", amount=5000
    )
    entries = (await session.execute(select(LedgerEntry))).scalars().all()
    assert entries == []


async def test_clear_hold_skips_when_auth_has_no_card_id(session):
    await auth_repository.create(
        session,
        idempotency_key="idem-001",
        decision=IssuerAuthDecision.APPROVED,
        decline_reason=None,
        amount=5000,
        currency="usd",
        card_id=None,
    )
    await settlement_service.clear_hold(
        session, idempotency_key="idem-001", amount=5000
    )
    entries = (await session.execute(select(LedgerEntry))).scalars().all()
    assert entries == []


# -- ledger invariants --


async def test_ledger_invariant_full_lifecycle_nets_to_zero(
    session, card, approved_auth
):
    await settlement_service.clear_hold(
        session, idempotency_key="idem-001", amount=5000
    )
    entries = (await session.execute(select(LedgerEntry))).scalars().all()
    assert sum(e.amount for e in entries) == 0


async def test_ledger_invariant_card_accounts_net_to_zero(session, card, approved_auth):
    await settlement_service.clear_hold(
        session, idempotency_key="idem-001", amount=5000
    )
    entries = (await session.execute(select(LedgerEntry))).scalars().all()
    card_amounts = [
        e.amount
        for e in entries
        if e.account_id
        in (card.available_balance_account_id, card.pending_hold_account_id)
    ]
    assert sum(card_amounts) == 0
