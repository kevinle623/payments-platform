import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.outbox.models import OutboxEventStatus, OutboxEventType


class OutboxEventDTO(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    event_type: OutboxEventType
    payload: dict
    status: OutboxEventStatus
    created_at: datetime
    published_at: datetime | None
