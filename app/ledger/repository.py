import uuid

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.ledger.models import LedgerAccount, LedgerEntry, LedgerTransaction
from app.ledger.schemas import (
    AccountBalanceResponse,
    LedgerAccountResponse,
    LedgerEntryDTO,
    LedgerTransactionResponse,
)
from shared.enum.currency import Currency


async def get_account(
    session: AsyncSession, account_id: uuid.UUID
) -> LedgerAccountResponse | None:
    result = await session.execute(
        select(LedgerAccount).where(LedgerAccount.id == account_id)
    )
    orm_object = result.scalar_one_or_none()
    if orm_object is None:
        return None
    return LedgerAccountResponse.model_validate(orm_object)


async def create_transaction(
    session: AsyncSession,
    description: str,
    entries: list[LedgerEntryDTO],
) -> LedgerTransactionResponse:
    transaction = LedgerTransaction(description=description)
    session.add(transaction)
    await session.flush()  # get transaction.id before creating entries

    for entry in entries:
        session.add(
            LedgerEntry(
                transaction_id=transaction.id,
                account_id=entry.account_id,
                amount=entry.amount,
            )
        )

    await session.flush()

    result = await session.execute(
        select(LedgerTransaction)
        .options(selectinload(LedgerTransaction.entries))
        .where(LedgerTransaction.id == transaction.id)
    )
    orm_object = result.scalar_one()
    return LedgerTransactionResponse.model_validate(orm_object)


async def get_transaction_with_entries(
    session: AsyncSession, transaction_id: uuid.UUID
) -> LedgerTransactionResponse | None:
    result = await session.execute(
        select(LedgerTransaction)
        .options(selectinload(LedgerTransaction.entries))
        .where(LedgerTransaction.id == transaction_id)
    )
    orm_object = result.scalar_one_or_none()
    if orm_object is None:
        return None
    return LedgerTransactionResponse.model_validate(orm_object)


async def get_account_balance(
    session: AsyncSession,
    account_id: uuid.UUID,
    currency: Currency,
) -> AccountBalanceResponse:
    result = await session.execute(
        select(func.coalesce(func.sum(LedgerEntry.amount), 0)).where(
            LedgerEntry.account_id == account_id, LedgerEntry.currency == currency
        )
    )
    balance = result.scalar_one()
    return AccountBalanceResponse(
        account_id=account_id, balance=balance, currency=Currency.USD
    )


async def get_entries_by_transaction(
    session: AsyncSession, transaction_id: uuid.UUID
) -> list[LedgerEntryDTO]:
    result = await session.execute(
        select(LedgerEntry).where(LedgerEntry.transaction_id == transaction_id)
    )
    return [
        LedgerEntryDTO(account_id=e.account_id, amount=e.amount)
        for e in result.scalars().all()
    ]
