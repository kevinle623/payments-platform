import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class ReconciliationRunDTO(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    started_at: datetime
    completed_at: datetime | None
    checked: int
    mismatches: int


class ReconciliationDiscrepancyDTO(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    run_id: uuid.UUID
    payment_id: uuid.UUID
    processor_payment_id: str
    our_status: str
    stripe_status: str
    detected_at: datetime
