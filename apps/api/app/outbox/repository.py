import uuid
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.outbox.models import OutboxEvent, OutboxEventStatus, OutboxEventType
from app.outbox.schemas import OutboxEventDTO

_POLL_BATCH_SIZE = 100


async def create(
    session: AsyncSession,
    event_type: OutboxEventType,
    payload: dict,
) -> OutboxEventDTO:
    event = OutboxEvent(
        event_type=event_type,
        payload=payload,
        status=OutboxEventStatus.PENDING,
    )
    session.add(event)
    await session.flush()
    return OutboxEventDTO.model_validate(event)


async def get_pending(
    session: AsyncSession,
) -> list[OutboxEventDTO]:
    result = await session.execute(
        select(OutboxEvent)
        .where(OutboxEvent.status == OutboxEventStatus.PENDING)
        .order_by(OutboxEvent.created_at)
        .limit(_POLL_BATCH_SIZE)
    )
    return [OutboxEventDTO.model_validate(row) for row in result.scalars().all()]


async def mark_published(
    session: AsyncSession,
    event_id: uuid.UUID,
) -> None:
    result = await session.execute(
        select(OutboxEvent).where(OutboxEvent.id == event_id)
    )
    event = result.scalar_one()
    event.status = OutboxEventStatus.PUBLISHED
    event.published_at = datetime.now(timezone.utc)
    await session.flush()


async def mark_failed(
    session: AsyncSession,
    event_id: uuid.UUID,
) -> None:
    result = await session.execute(
        select(OutboxEvent).where(OutboxEvent.id == event_id)
    )
    event = result.scalar_one()
    event.status = OutboxEventStatus.FAILED
    await session.flush()
