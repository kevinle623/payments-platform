import uuid

import pytest

from app.ledger import service
from app.ledger.models import LedgerAccount
from app.ledger.schemas import LedgerEntryDTO
from shared.enum.currency import Currency
from shared.exceptions import LedgerImbalanceError


async def test_record_transaction_fails_if_entries_dont_balance(session):
    entries = [
        LedgerEntryDTO(account_id=uuid.uuid4(), amount=100),
        # missing the credit side -- should fail
    ]
    with pytest.raises(LedgerImbalanceError):
        await service._record_transaction(session, "test", entries)


async def test_record_transaction_succeeds_when_entries_balance(session):
    # create real accounts first
    account_a = LedgerAccount(
        name="expenses", account_type="expense", currency=Currency.USD
    )
    account_b = LedgerAccount(
        name="liability", account_type="liability", currency=Currency.USD
    )
    session.add(account_a)
    session.add(account_b)
    await session.flush()

    entries = [
        LedgerEntryDTO(account_id=account_a.id, amount=100),
        LedgerEntryDTO(account_id=account_b.id, amount=-100),
    ]
    result = await service._record_transaction(session, "test charge", entries)
    assert result.description == "test charge"
    assert len(result.entries) == 2
    assert sum(e.amount for e in result.entries) == 0


async def test_record_authorization_creates_correct_entries(session):
    expense = LedgerAccount(
        name="expenses", account_type="expense", currency=Currency.USD
    )
    liability = LedgerAccount(
        name="liability", account_type="liability", currency=Currency.USD
    )
    session.add(expense)
    session.add(liability)
    await session.flush()

    result = await service.record_authorization(
        session,
        expense_account_id=expense.id,
        liability_account_id=liability.id,
        amount=5000,
        description="auth for $50 charge",
    )

    assert len(result.entries) == 2
    amounts = {e.account_id: e.amount for e in result.entries}
    assert amounts[expense.id] == 5000
    assert amounts[liability.id] == -5000


async def test_record_transaction_fails_with_three_unbalanced_entries(session):
    account_a = LedgerAccount(name="a", account_type="expense", currency=Currency.USD)
    account_b = LedgerAccount(name="b", account_type="liability", currency=Currency.USD)
    session.add(account_a)
    session.add(account_b)
    await session.flush()

    entries = [
        LedgerEntryDTO(account_id=account_a.id, amount=100),
        LedgerEntryDTO(account_id=account_b.id, amount=-50),  # only credits half
    ]
    with pytest.raises(LedgerImbalanceError):
        await service._record_transaction(session, "bad transaction", entries)


async def test_get_balance_returns_correct_sum(session):
    account = LedgerAccount(
        name="expenses", account_type="expense", currency=Currency.USD
    )
    contra = LedgerAccount(
        name="liability", account_type="liability", currency=Currency.USD
    )
    session.add(account)
    session.add(contra)
    await session.flush()

    await service.record_authorization(
        session,
        expense_account_id=account.id,
        liability_account_id=contra.id,
        amount=5000,
        description="first charge",
    )
    await service.record_authorization(
        session,
        expense_account_id=account.id,
        liability_account_id=contra.id,
        amount=3000,
        description="second charge",
    )

    balance = await service.get_balance(session, account.id, Currency.USD)
    assert balance.balance == 8000
