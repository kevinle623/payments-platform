import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.fraud.models import RiskLevel


class FraudSignalDTO(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    payment_id: uuid.UUID
    risk_level: RiskLevel
    amount: int
    currency: str
    flagged_at: datetime
