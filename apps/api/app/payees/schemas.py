import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.payees.models import PayeeType
from shared.enums.currency import Currency


class CreatePayeeRequest(BaseModel):
    name: str
    payee_type: PayeeType
    account_number: str
    routing_number: str
    currency: Currency


class PayeeDTO(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    payee_type: PayeeType
    account_number: str
    routing_number: str
    currency: str
    created_at: datetime
