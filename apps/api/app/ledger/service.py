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
from shared.logger import get_logger

logger = get_logger(__name__)


async def _record_transaction(
    session: AsyncSession,
    description: str,
    entries: list[LedgerEntryDTO],
) -> LedgerTransactionResponse:
    total = sum(e.amount for e in entries)
    if total != 0:
        logger.error(
            "ledger imbalance detected | description=%s sum=%d entry_count=%d",
            description,
            total,
            len(entries),
        )
        raise LedgerImbalanceError(
            f"Ledger entries do not balance: sum={total}. "
            "Debits and credits must cancel out."
        )
    result = await repository.create_transaction(session, description, entries)
    logger.debug(
        "ledger transaction created | transaction_id=%s description=%s entry_count=%d",
        result.id,
        description,
        len(entries),
    )
    return result


async def record_authorization(
    session: AsyncSession,
    expense_account_id: uuid.UUID,
    liability_account_id: uuid.UUID,
    amount: int,
    description: str,
) -> LedgerTransactionResponse:
    """Debit expenses, credit liability -- money is spoken for but not yet settled."""
    logger.info(
        "recording authorization | amount=%d expense_account=%s liability_account=%s",
        amount,
        expense_account_id,
        liability_account_id,
    )
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
    logger.info(
        "recording settlement | amount=%d liability_account=%s cash_account=%s",
        amount,
        liability_account_id,
        cash_account_id,
    )
    entries = [
        LedgerEntryDTO(account_id=liability_account_id, amount=amount),
        LedgerEntryDTO(account_id=cash_account_id, amount=-amount),
    ]
    return await _record_transaction(session, description, entries)


async def record_hold(
    session: AsyncSession,
    available_balance_account_id: uuid.UUID,
    pending_hold_account_id: uuid.UUID,
    amount: int,
    description: str,
) -> LedgerTransactionResponse:
    """Credit available balance (reduce available credit), debit pending hold."""
    logger.info(
        "recording hold | amount=%d available_account=%s pending_account=%s",
        amount,
        available_balance_account_id,
        pending_hold_account_id,
    )
    entries = [
        LedgerEntryDTO(account_id=available_balance_account_id, amount=-amount),
        LedgerEntryDTO(account_id=pending_hold_account_id, amount=amount),
    ]
    return await _record_transaction(session, description, entries)


async def get_balance(
    session: AsyncSession,
    account_id: uuid.UUID,
    currency: Currency,
) -> AccountBalanceResponse:
    return await repository.get_account_balance(session, account_id, currency)
