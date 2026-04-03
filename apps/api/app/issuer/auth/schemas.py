import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.issuer.auth.models import IssuerAuthDecision


class IssuerAuthorizationDTO(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    idempotency_key: str
    decision: IssuerAuthDecision
    decline_reason: str | None
    amount: int
    currency: str
    created_at: datetime
