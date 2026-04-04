import uuid
from datetime import datetime, timezone
from enum import StrEnum

from sqlalchemy import DateTime, Index, String
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from shared.db.base import Base


class OutboxEventType(StrEnum):
    PAYMENT_AUTHORIZED = "payment.authorized"
    PAYMENT_SETTLED = "payment.settled"
    PAYMENT_REFUNDED = "payment.refunded"


class OutboxEventStatus(StrEnum):
    PENDING = "pending"
    PUBLISHED = "published"
    FAILED = "failed"


class OutboxEvent(Base):
    __tablename__ = "outbox_events"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    event_type: Mapped[str] = mapped_column(String, nullable=False)
    payload: Mapped[dict] = mapped_column(JSONB, nullable=False)
    status: Mapped[str] = mapped_column(
        String, nullable=False, default=OutboxEventStatus.PENDING
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    published_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    __table_args__ = (
        # worker polls on status=pending ordered by created_at
        Index("ix_outbox_events_status_created_at", "status", "created_at"),
    )
