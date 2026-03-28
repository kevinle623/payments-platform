import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class LedgerAccountResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    account_type: str
    currency: str
    created_at: datetime


class LedgerEntryDTO(BaseModel):
    account_id: uuid.UUID
    amount: int  # positive = debit, negative = credit


class LedgerEntryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    account_id: uuid.UUID
    amount: int
    currency: str
    created_at: datetime


class LedgerTransactionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    description: str
    entries: list[LedgerEntryResponse]
    created_at: datetime


class AccountBalanceResponse(BaseModel):
    account_id: uuid.UUID
    balance: int
    currency: str
