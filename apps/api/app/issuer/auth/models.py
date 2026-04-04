import uuid
from datetime import datetime, timezone
from enum import StrEnum

from sqlalchemy import DateTime, Index, Integer, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from shared.db.base import Base


class IssuerAuthDecision(StrEnum):
    APPROVED = "approved"
    DECLINED = "declined"


class IssuerAuthorization(Base):
    __tablename__ = "issuer_authorizations"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )

    # ties this authorization record back to the payment request
    idempotency_key: Mapped[str] = mapped_column(String, nullable=False, unique=True)

    # card that was authorized against -- None for payments without a card
    card_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)

    decision: Mapped[str] = mapped_column(String, nullable=False)
    decline_reason: Mapped[str | None] = mapped_column(String, nullable=True)

    amount: Mapped[int] = mapped_column(Integer, nullable=False)
    currency: Mapped[str] = mapped_column(String(3), nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    __table_args__ = (
        Index("ix_issuer_authorizations_idempotency_key", "idempotency_key"),
        Index("ix_issuer_authorizations_decision", "decision"),
    )
