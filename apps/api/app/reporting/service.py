import uuid
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession

from app.reporting import repository
from app.reporting.schemas import ReportingEventDTO, ReportingSummaryEntry


async def record_event(
    session: AsyncSession,
    event_type: str,
    payment_id: uuid.UUID,
    amount: int,
    currency: str,
) -> ReportingEventDTO:
    event = await repository.create(
        session=session,
        event_type=event_type,
        payment_id=payment_id,
        amount=amount,
        currency=currency,
    )
    await session.commit()
    return event


async def get_summary(
    session: AsyncSession,
    since: datetime | None = None,
    until: datetime | None = None,
) -> list[ReportingSummaryEntry]:
    return await repository.get_daily_summary(
        session=session,
        since=since,
        until=until,
    )
