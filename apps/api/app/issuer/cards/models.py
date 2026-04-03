import uuid
from datetime import datetime, timezone
from enum import StrEnum

from sqlalchemy import DateTime, ForeignKey, Index, Integer, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from shared.db.base import Base


class CardholderStatus(StrEnum):
    ACTIVE = "active"
    SUSPENDED = "suspended"
    CLOSED = "closed"


class CardStatus(StrEnum):
    ACTIVE = "active"
    FROZEN = "frozen"
    CLOSED = "closed"


class Cardholder(Base):
    __tablename__ = "cardholders"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    name: Mapped[str] = mapped_column(String, nullable=False)
    email: Mapped[str] = mapped_column(String, nullable=False, unique=True)
    status: Mapped[str] = mapped_column(
        String, nullable=False, default=CardholderStatus.ACTIVE
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    cards: Mapped[list["Card"]] = relationship(back_populates="cardholder")

    __table_args__ = (Index("ix_cardholders_email", "email"),)


class Card(Base):
    __tablename__ = "cards"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    cardholder_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("cardholders.id"), nullable=False
    )

    # credit limit in cents -- the maximum the cardholder can spend
    credit_limit: Mapped[int] = mapped_column(Integer, nullable=False)

    # ledger account IDs -- created automatically when the card is issued
    # available_balance_account: tracks reductions to available credit (holds place negative entries)
    # pending_hold_account: tracks authorized-but-not-settled amounts
    available_balance_account_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), nullable=False
    )
    pending_hold_account_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), nullable=False
    )

    currency: Mapped[str] = mapped_column(String(3), nullable=False)
    status: Mapped[str] = mapped_column(
        String, nullable=False, default=CardStatus.ACTIVE
    )
    last_four: Mapped[str | None] = mapped_column(String(4), nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    cardholder: Mapped["Cardholder"] = relationship(back_populates="cards")

    __table_args__ = (
        Index("ix_cards_cardholder_id", "cardholder_id"),
        Index("ix_cards_status", "status"),
    )
