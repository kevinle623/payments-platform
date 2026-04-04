import uuid
from unittest.mock import AsyncMock, patch

import pytest
from sqlalchemy import select

from app.issuer.cards import service as cards_service
from app.ledger.models import LedgerAccount, LedgerEntry
from app.payments import service
from app.payments.models import Payment
from shared.enums.currency import Currency
from shared.exceptions import PaymentDeclinedException
from shared.processors.base import PaymentIntent, PaymentProcessor, PaymentStatus


@pytest.fixture
def mock_processor():
    processor = AsyncMock(spec=PaymentProcessor)
    processor.create_payment_intent.return_value = PaymentIntent(
        processor_id="pi_test_123",
        client_secret="pi_test_123_secret",
        status=PaymentStatus.PENDING,
        amount=5000,
        currency="usd",
        metadata={},
    )
    return processor


@pytest.fixture
async def ledger_accounts(session):
    expense = LedgerAccount(
        name="expenses", account_type="expense", currency=Currency.USD
    )
    liability = LedgerAccount(
        name="liability", account_type="liability", currency=Currency.USD
    )
    cash = LedgerAccount(name="cash", account_type="asset", currency=Currency.USD)
    session.add_all([expense, liability, cash])
    await session.flush()
    return expense, liability, cash


async def test_authorize_creates_payment_and_ledger_entries(
    session, mock_processor, ledger_accounts
):
    expense, liability, _ = ledger_accounts

    response = await service.authorize(
        session=session,
        request=_authorize_request(),
        processor=mock_processor,
        expense_account_id=expense.id,
        liability_account_id=liability.id,
    )

    assert response.processor_payment_id == "pi_test_123"
    assert response.client_secret == "pi_test_123_secret"
    assert response.status == PaymentStatus.PENDING
    assert response.amount == 5000

    # payment row written
    result = await session.execute(
        select(Payment).where(Payment.processor_payment_id == "pi_test_123")
    )
    payment = result.scalar_one()
    assert payment.amount == 5000

    # two ledger entries written -- one debit, one credit
    result = await session.execute(select(LedgerEntry))
    entries = result.scalars().all()
    assert len(entries) == 2
    amounts = {e.account_id: e.amount for e in entries}
    assert amounts[expense.id] == 5000
    assert amounts[liability.id] == -5000


async def test_authorize_idempotency_returns_existing(
    session, mock_processor, ledger_accounts
):
    expense, liability, _ = ledger_accounts
    request = _authorize_request()

    await service.authorize(
        session=session,
        request=request,
        processor=mock_processor,
        expense_account_id=expense.id,
        liability_account_id=liability.id,
    )
    await service.authorize(
        session=session,
        request=request,
        processor=mock_processor,
        expense_account_id=expense.id,
        liability_account_id=liability.id,
    )

    # processor only called once
    mock_processor.create_payment_intent.assert_called_once()

    # only one payment row
    result = await session.execute(select(Payment))
    payments = result.scalars().all()
    assert len(payments) == 1


async def test_authorize_processor_failure_rolls_back(
    session, mock_processor, ledger_accounts
):
    expense, liability, _ = ledger_accounts
    mock_processor.create_payment_intent.side_effect = Exception("stripe down")

    with pytest.raises(Exception, match="stripe down"):
        await service.authorize(
            session=session,
            request=_authorize_request(),
            processor=mock_processor,
            expense_account_id=expense.id,
            liability_account_id=liability.id,
        )

    result = await session.execute(select(Payment))
    assert result.scalars().all() == []


async def test_handle_payment_succeeded_settles_record_and_ledger(
    session, mock_processor, ledger_accounts
):
    expense, liability, cash = ledger_accounts

    # seed a payment first
    await service.authorize(
        session=session,
        request=_authorize_request(),
        processor=mock_processor,
        expense_account_id=expense.id,
        liability_account_id=liability.id,
    )

    await service.handle_payment_succeeded(
        session=session,
        processor_payment_id="pi_test_123",
        liability_account_id=liability.id,
        cash_account_id=cash.id,
    )

    result = await session.execute(
        select(Payment).where(Payment.processor_payment_id == "pi_test_123")
    )
    payment = result.scalar_one()
    assert payment.status == PaymentStatus.SUCCEEDED

    # 4 entries total: 2 from auth, 2 from settlement
    result = await session.execute(select(LedgerEntry))
    entries = result.scalars().all()
    assert len(entries) == 4


async def test_handle_payment_succeeded_unknown_payment_is_noop(
    session, ledger_accounts
):
    _, liability, cash = ledger_accounts

    # should not raise
    await service.handle_payment_succeeded(
        session=session,
        processor_payment_id="pi_unknown",
        liability_account_id=liability.id,
        cash_account_id=cash.id,
    )

    result = await session.execute(select(LedgerEntry))
    assert result.scalars().all() == []


async def test_handle_payment_refunded_marks_record_refunded(
    session, mock_processor, ledger_accounts
):
    expense, liability, _ = ledger_accounts

    await service.authorize(
        session=session,
        request=_authorize_request(),
        processor=mock_processor,
        expense_account_id=expense.id,
        liability_account_id=liability.id,
    )

    await service.handle_payment_refunded(
        session=session,
        processor_payment_id="pi_test_123",
    )

    result = await session.execute(
        select(Payment).where(Payment.processor_payment_id == "pi_test_123")
    )
    payment = result.scalar_one()
    assert payment.status == PaymentStatus.REFUNDED


# -- card-integrated payment tests --


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


async def test_authorize_with_card_writes_issuer_and_acquiring_ledger_entries(
    session, mock_processor, ledger_accounts, card
):
    expense, liability, _ = ledger_accounts

    await service.authorize(
        session=session,
        request=_authorize_request(card_id=card.id),
        processor=mock_processor,
        expense_account_id=expense.id,
        liability_account_id=liability.id,
    )

    entries = (await session.execute(select(LedgerEntry))).scalars().all()
    # 2 issuer (hold) + 2 acquiring (auth) = 4 total
    assert len(entries) == 4
    assert sum(e.amount for e in entries) == 0


async def test_authorize_with_card_declined_raises_and_no_stripe_call(
    session, mock_processor, ledger_accounts, card
):
    expense, liability, _ = ledger_accounts

    with pytest.raises(PaymentDeclinedException):
        await service.authorize(
            session=session,
            request=_authorize_request(
                amount=50000, card_id=card.id
            ),  # $500 > $100 limit
            processor=mock_processor,
            expense_account_id=expense.id,
            liability_account_id=liability.id,
        )

    mock_processor.create_payment_intent.assert_not_called()

    entries = (await session.execute(select(LedgerEntry))).scalars().all()
    assert entries == []


async def test_handle_payment_succeeded_with_card_clears_hold(
    session, mock_processor, ledger_accounts, card
):
    expense, liability, cash = ledger_accounts

    await service.authorize(
        session=session,
        request=_authorize_request(card_id=card.id),
        processor=mock_processor,
        expense_account_id=expense.id,
        liability_account_id=liability.id,
    )
    await service.handle_payment_succeeded(
        session=session,
        processor_payment_id="pi_test_123",
        liability_account_id=liability.id,
        cash_account_id=cash.id,
    )

    entries = (await session.execute(select(LedgerEntry))).scalars().all()
    # 2 issuer hold + 2 acquiring auth + 2 acquiring settlement + 2 issuer clear = 8
    assert len(entries) == 8
    assert sum(e.amount for e in entries) == 0


# -- helpers --


def _authorize_request(amount: int = 5000, card_id: uuid.UUID | None = None):
    from app.payments.schemas import AuthorizeRequest

    return AuthorizeRequest(
        amount=amount,
        currency=Currency.USD,
        idempotency_key="idem-key-001",
        metadata={},
        card_id=card_id,
    )
