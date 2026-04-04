import uuid
from datetime import date, datetime

from pydantic import BaseModel, ConfigDict


class ReportingEventDTO(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    event_type: str
    payment_id: uuid.UUID
    amount: int
    currency: str
    recorded_at: datetime


class ReportingSummaryEntry(BaseModel):
    date: date
    event_type: str
    currency: str
    total_amount: int
    count: int
