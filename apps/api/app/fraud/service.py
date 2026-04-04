import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.fraud import repository
from app.fraud.models import RiskLevel
from app.fraud.schemas import FraudSignalDTO


async def create_signal(
    session: AsyncSession,
    payment_id: uuid.UUID,
    risk_level: RiskLevel,
    amount: int,
    currency: str,
) -> FraudSignalDTO:
    signal = await repository.create(
        session=session,
        payment_id=payment_id,
        risk_level=risk_level,
        amount=amount,
        currency=currency,
    )
    await session.commit()
    return signal


async def list_signals(
    session: AsyncSession,
    risk_level: RiskLevel | None = None,
    limit: int = 100,
    offset: int = 0,
) -> list[FraudSignalDTO]:
    return await repository.list_signals(
        session=session,
        risk_level=risk_level,
        limit=limit,
        offset=offset,
    )
