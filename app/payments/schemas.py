import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict

from shared.enums.currency import Currency
from shared.processors.base import PaymentStatus


class AuthorizeRequest(BaseModel):
    amount: int  # in cents
    currency: Currency
    idempotency_key: str
    metadata: dict = {}


class AuthorizeResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    processor_payment_id: str | None
    status: PaymentStatus
    amount: int
    currency: str
    idempotency_key: str
    created_at: datetime


class CaptureRequest(BaseModel):
    processor_payment_id: str


class CaptureResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    processor_payment_id: str
    status: PaymentStatus
    amount: int
    currency: str
    updated_at: datetime


class RefundRequest(BaseModel):
    processor_payment_id: str
    amount: int  # partial refunds supported -- must be <= original amount


class RefundResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    processor_payment_id: str
    status: PaymentStatus
    amount: int
    currency: str
    updated_at: datetime


class PaymentRecord(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    processor_payment_id: str | None
    status: PaymentStatus
    amount: int
    currency: str
    idempotency_key: str
    created_at: datetime
    updated_at: datetime
