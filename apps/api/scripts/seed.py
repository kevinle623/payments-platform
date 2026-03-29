import asyncio
import uuid

from app.ledger.models import AccountType, LedgerAccount
from shared.db.adapters.postgresql import AsyncSessionLocal
from shared.enums.currency import Currency
from shared.settings import CASH_ACCOUNT_ID, EXPENSE_ACCOUNT_ID, LIABILITY_ACCOUNT_ID

ACCOUNTS = [
    {"id": EXPENSE_ACCOUNT_ID, "name": "expenses", "account_type": AccountType.EXPENSE},
    {
        "id": LIABILITY_ACCOUNT_ID,
        "name": "liability",
        "account_type": AccountType.LIABILITY,
    },
    {"id": CASH_ACCOUNT_ID, "name": "cash", "account_type": AccountType.ASSET},
]


async def seed():
    async with AsyncSessionLocal() as session:
        for account_data in ACCOUNTS:
            account = LedgerAccount(
                id=uuid.UUID(account_data["id"]),
                name=account_data["name"],
                account_type=account_data["account_type"],
                currency=Currency.USD,
            )
            session.add(account)
        await session.commit()
        print("Seeded ledger accounts")


asyncio.run(seed())
