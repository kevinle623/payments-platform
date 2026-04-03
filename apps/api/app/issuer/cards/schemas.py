import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.issuer.cards.models import CardStatus, CardholderStatus
from shared.enums.currency import Currency


class CreateCardholderRequest(BaseModel):
    name: str
    email: str


class CardholderDTO(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    email: str
    status: CardholderStatus
    created_at: datetime


class CreateCardRequest(BaseModel):
    cardholder_id: uuid.UUID
    credit_limit: int  # in cents
    currency: Currency = Currency.USD
    last_four: str | None = None


class CardDTO(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    cardholder_id: uuid.UUID
    credit_limit: int
    available_balance_account_id: uuid.UUID
    pending_hold_account_id: uuid.UUID
    currency: str
    status: CardStatus
    last_four: str | None
    created_at: datetime
    updated_at: datetime


class CardBalanceResponse(BaseModel):
    card_id: uuid.UUID
    credit_limit: int
    available_credit: int  # credit_limit + balance(available_balance_account)
    pending_holds: int     # balance(pending_hold_account)
    currency: str
