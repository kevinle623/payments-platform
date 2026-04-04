import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class MCCBlockDTO(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    card_id: uuid.UUID
    mcc: str
    created_at: datetime


class CreateMCCBlockRequest(BaseModel):
    mcc: str  # 4-digit merchant category code


class VelocityRuleDTO(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    card_id: uuid.UUID
    max_amount: int  # in cents
    window_seconds: int
    created_at: datetime


class CreateVelocityRuleRequest(BaseModel):
    max_amount: int  # in cents
    window_seconds: int
