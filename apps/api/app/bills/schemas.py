import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.bills.models import BillFrequency, BillPaymentStatus, BillStatus
from shared.enums.currency import Currency


class CreateBillRequest(BaseModel):
    payee_id: uuid.UUID
    card_id: uuid.UUID | None = None
    amount: int
    currency: Currency
    frequency: BillFrequency
    next_due_date: datetime


class UpdateBillRequest(BaseModel):
    card_id: uuid.UUID | None = None
    amount: int | None = None
    frequency: BillFrequency | None = None
    next_due_date: datetime | None = None
    status: BillStatus | None = None


class BillDTO(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    payee_id: uuid.UUID
    card_id: uuid.UUID | None
    amount: int
    currency: str
    frequency: BillFrequency
    next_due_date: datetime
    status: BillStatus
    created_at: datetime
    updated_at: datetime


class BillPaymentDTO(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    bill_id: uuid.UUID
    payment_id: uuid.UUID | None
    status: BillPaymentStatus
    executed_at: datetime


class BillDetailResponse(BaseModel):
    bill: BillDTO
    payments: list[BillPaymentDTO]


class BillExecutionResponse(BaseModel):
    bill: BillDTO
    bill_payment: BillPaymentDTO
