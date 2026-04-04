import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.fraud.models import FraudSignal, RiskLevel
from app.fraud.schemas import FraudSignalDTO


async def create(
    session: AsyncSession,
    payment_id: uuid.UUID,
    risk_level: RiskLevel,
    amount: int,
    currency: str,
) -> FraudSignalDTO:
    signal = FraudSignal(
        payment_id=payment_id,
        risk_level=risk_level,
        amount=amount,
        currency=currency,
    )
    session.add(signal)
    await session.flush()
    return FraudSignalDTO.model_validate(signal)


async def list_signals(
    session: AsyncSession,
    risk_level: RiskLevel | None = None,
    limit: int = 100,
    offset: int = 0,
) -> list[FraudSignalDTO]:
    query = select(FraudSignal).order_by(FraudSignal.flagged_at.desc())
    if risk_level is not None:
        query = query.where(FraudSignal.risk_level == risk_level)
    query = query.limit(limit).offset(offset)
    result = await session.execute(query)
    return [FraudSignalDTO.model_validate(row) for row in result.scalars().all()]
