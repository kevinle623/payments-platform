import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, Index, Integer, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from shared.db.base import Base
from shared.processors.base import PaymentStatus


class Payment(Base):
    __tablename__ = "payments"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )

    # idempotency key -- caller provides this to prevent duplicate payments
    idempotency_key: Mapped[str] = mapped_column(String, nullable=False, unique=True)

    # processor fields -- what Stripe knows about this payment
    processor_payment_id: Mapped[str] = mapped_column(String, nullable=True)
    processor: Mapped[str] = mapped_column(String, nullable=False)

    # payment details
    amount: Mapped[int] = mapped_column(Integer, nullable=False)  # in cents
    currency: Mapped[str] = mapped_column(String(3), nullable=False)
    status: Mapped[str] = mapped_column(
        String, nullable=False, default=PaymentStatus.PENDING
    )

    # link to the ledger transaction created for this payment
    ledger_transaction_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), nullable=True
    )

    # timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    __table_args__ = (
        # idempotency lookups -- most frequent query
        Index("ix_payments_idempotency_key", "idempotency_key"),
        # webhook handler looks up by processor_payment_id
        Index("ix_payments_processor_payment_id", "processor_payment_id"),
        # status filtering -- e.g. find all pending payments
        Index("ix_payments_status", "status"),
        # reconciliation -- payments within a time range
        Index("ix_payments_created_at", "created_at"),
    )
