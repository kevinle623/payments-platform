import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.outbox import repository
from app.outbox.models import OutboxEventType
from app.outbox.schemas import OutboxEventDTO
from shared.logger import get_logger

logger = get_logger(__name__)


async def publish_event(
    session: AsyncSession,
    event_type: OutboxEventType,
    payload: dict,
) -> OutboxEventDTO:
    """
    Write an outbox event in the same transaction as the caller.
    The event will be picked up and published to RabbitMQ by the outbox poller worker.
    No commit here -- the caller owns the transaction boundary.
    """
    event = await repository.create(session, event_type=event_type, payload=payload)
    logger.debug(
        "outbox event queued | event_id=%s event_type=%s", event.id, event_type
    )
    return event


async def list_events_for_payment(
    session: AsyncSession,
    payment_id: uuid.UUID,
    limit: int = 100,
    offset: int = 0,
) -> list[OutboxEventDTO]:
    return await repository.list_by_payment_id(
        session=session,
        payment_id=payment_id,
        limit=limit,
        offset=offset,
    )
