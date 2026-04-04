import uuid
from datetime import date, datetime, timezone

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.reporting.models import ReportingEvent
from app.reporting.schemas import ReportingEventDTO, ReportingSummaryEntry


async def create(
    session: AsyncSession,
    event_type: str,
    payment_id: uuid.UUID,
    amount: int,
    currency: str,
) -> ReportingEventDTO:
    event = ReportingEvent(
        event_type=event_type,
        payment_id=payment_id,
        amount=amount,
        currency=currency,
    )
    session.add(event)
    await session.flush()
    return ReportingEventDTO.model_validate(event)


async def get_daily_summary(
    session: AsyncSession,
    since: datetime | None = None,
    until: datetime | None = None,
) -> list[ReportingSummaryEntry]:
    day_col = func.date(ReportingEvent.recorded_at).label("date")

    query = (
        select(
            day_col,
            ReportingEvent.event_type,
            ReportingEvent.currency,
            func.sum(ReportingEvent.amount).label("total_amount"),
            func.count(ReportingEvent.id).label("count"),
        )
        .group_by(
            func.date(ReportingEvent.recorded_at),
            ReportingEvent.event_type,
            ReportingEvent.currency,
        )
        .order_by(func.date(ReportingEvent.recorded_at).desc())
    )

    if since is not None:
        query = query.where(ReportingEvent.recorded_at >= since)
    if until is not None:
        query = query.where(ReportingEvent.recorded_at <= until)

    result = await session.execute(query)
    return [
        ReportingSummaryEntry(
            date=row.date,
            event_type=row.event_type,
            currency=row.currency,
            total_amount=row.total_amount,
            count=row.count,
        )
        for row in result.all()
    ]
