import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey, Index, Integer, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from shared.db.base import Base


class ReconciliationRun(Base):
    __tablename__ = "reconciliation_runs"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    # total payments checked in this run
    checked: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    # number of mismatches found
    mismatches: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    discrepancies: Mapped[list["ReconciliationDiscrepancy"]] = relationship(
        back_populates="run"
    )

    __table_args__ = (
        Index("ix_reconciliation_runs_started_at", "started_at"),
    )


class ReconciliationDiscrepancy(Base):
    __tablename__ = "reconciliation_discrepancies"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    run_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("reconciliation_runs.id"), nullable=False
    )
    payment_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    processor_payment_id: Mapped[str] = mapped_column(String, nullable=False)
    our_status: Mapped[str] = mapped_column(String, nullable=False)
    stripe_status: Mapped[str] = mapped_column(String, nullable=False)
    detected_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    run: Mapped["ReconciliationRun"] = relationship(back_populates="discrepancies")

    __table_args__ = (
        Index("ix_reconciliation_discrepancies_run_id", "run_id"),
        Index("ix_reconciliation_discrepancies_payment_id", "payment_id"),
    )
