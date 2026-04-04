import uuid
from datetime import datetime, timezone
from enum import StrEnum

from sqlalchemy import DateTime, Index, Integer, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from shared.db.base import Base


class RiskLevel(StrEnum):
    LOW = "low"
    HIGH = "high"


class FraudSignal(Base):
    __tablename__ = "fraud_signals"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )

    # the payment that triggered this signal
    payment_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)

    risk_level: Mapped[str] = mapped_column(String, nullable=False)
    amount: Mapped[int] = mapped_column(Integer, nullable=False)  # in cents
    currency: Mapped[str] = mapped_column(String(3), nullable=False)

    flagged_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    __table_args__ = (
        # dashboard queries filter by risk_level and sort by flagged_at
        Index("ix_fraud_signals_risk_level_flagged_at", "risk_level", "flagged_at"),
    )
