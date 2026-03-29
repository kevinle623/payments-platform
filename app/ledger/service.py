import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.ledger import repository
from app.ledger.schemas import (
    AccountBalanceResponse,
    LedgerEntryDTO,
    LedgerTransactionResponse,
)
from shared.enums.currency import Currency
from shared.exceptions import LedgerImbalanceError


async def _record_transaction(
    session: AsyncSession,
    description: str,
    entries: list[LedgerEntryDTO],
) -> LedgerTransactionResponse:
    total = sum(e.amount for e in entries)
    if total != 0:
        raise LedgerImbalanceError(
            f"Ledger entries do not balance: sum={total}. "
            "Debits and credits must cancel out."
        )
    return await repository.create_transaction(session, description, entries)


async def record_authorization(
    session: AsyncSession,
    expense_account_id: uuid.UUID,
    liability_account_id: uuid.UUID,
    amount: int,
    description: str,
) -> LedgerTransactionResponse:
    """Debit expenses, credit liability -- money is spoken for but not yet settled."""
    entries = [
        LedgerEntryDTO(account_id=expense_account_id, amount=amount),
        LedgerEntryDTO(account_id=liability_account_id, amount=-amount),
    ]
    return await _record_transaction(session, description, entries)


async def record_settlement(
    session: AsyncSession,
    liability_account_id: uuid.UUID,
    cash_account_id: uuid.UUID,
    amount: int,
    description: str,
) -> LedgerTransactionResponse:
    """Debit liability, credit cash -- money has actually moved."""
    entries = [
        LedgerEntryDTO(account_id=liability_account_id, amount=amount),
        LedgerEntryDTO(account_id=cash_account_id, amount=-amount),
    ]
    return await _record_transaction(session, description, entries)


async def get_balance(
    session: AsyncSession,
    account_id: uuid.UUID,
    currency: Currency,
) -> AccountBalanceResponse:
    return await repository.get_account_balance(session, account_id, currency)
