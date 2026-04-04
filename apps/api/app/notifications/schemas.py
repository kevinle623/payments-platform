import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.notifications.models import NotificationChannel


class NotificationLogDTO(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    cardholder_id: uuid.UUID | None
    event_type: str
    channel: NotificationChannel
    message: str
    sent_at: datetime
