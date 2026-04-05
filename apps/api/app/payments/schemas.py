import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.issuer.auth.schemas import IssuerAuthorizationDTO
from app.ledger.schemas import LedgerTransactionResponse
from app.outbox.schemas import OutboxEventDTO
from shared.enums.currency import Currency
from shared.processors.base import PaymentStatus


class AuthorizeRequest(BaseModel):
    amount: int  # in cents
    currency: Currency
    idempotency_key: str
    metadata: dict = {}
    card_id: uuid.UUID | None = (
        None  # optional -- triggers issuer controls when provided
    )


class AuthorizeResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    processor_payment_id: str | None
    client_secret: str | None = None
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


class PaymentDetailResponse(BaseModel):
    payment: PaymentRecord
    ledger_transactions: list[LedgerTransactionResponse]
    outbox_events: list[OutboxEventDTO]
    issuer_authorization: IssuerAuthorizationDTO | None
