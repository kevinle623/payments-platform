import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.notifications.models import NotificationChannel, NotificationLog
from app.notifications.schemas import NotificationLogDTO


async def create(
    session: AsyncSession,
    event_type: str,
    channel: NotificationChannel,
    message: str,
    cardholder_id: uuid.UUID | None = None,
) -> NotificationLogDTO:
    log = NotificationLog(
        cardholder_id=cardholder_id,
        event_type=event_type,
        channel=channel,
        message=message,
    )
    session.add(log)
    await session.flush()
    return NotificationLogDTO.model_validate(log)
