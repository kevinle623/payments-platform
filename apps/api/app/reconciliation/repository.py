import uuid
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.reconciliation.models import ReconciliationDiscrepancy, ReconciliationRun
from app.reconciliation.schemas import ReconciliationDiscrepancyDTO, ReconciliationRunDTO


# -- runs --


async def create_run(session: AsyncSession) -> ReconciliationRunDTO:
    run = ReconciliationRun()
    session.add(run)
    await session.flush()
    return ReconciliationRunDTO.model_validate(run)


async def complete_run(
    session: AsyncSession,
    run_id: uuid.UUID,
    checked: int,
    mismatches: int,
) -> ReconciliationRunDTO | None:
    result = await session.execute(
        select(ReconciliationRun).where(ReconciliationRun.id == run_id)
    )
    run = result.scalar_one_or_none()
    if run is None:
        return None
    run.completed_at = datetime.now(timezone.utc)
    run.checked = checked
    run.mismatches = mismatches
    await session.flush()
    return ReconciliationRunDTO.model_validate(run)


async def list_runs(
    session: AsyncSession,
    limit: int = 50,
    offset: int = 0,
) -> list[ReconciliationRunDTO]:
    result = await session.execute(
        select(ReconciliationRun)
        .order_by(ReconciliationRun.started_at.desc())
        .limit(limit)
        .offset(offset)
    )
    return [ReconciliationRunDTO.model_validate(row) for row in result.scalars().all()]


# -- discrepancies --


async def create_discrepancy(
    session: AsyncSession,
    run_id: uuid.UUID,
    payment_id: uuid.UUID,
    processor_payment_id: str,
    our_status: str,
    stripe_status: str,
) -> ReconciliationDiscrepancyDTO:
    discrepancy = ReconciliationDiscrepancy(
        run_id=run_id,
        payment_id=payment_id,
        processor_payment_id=processor_payment_id,
        our_status=our_status,
        stripe_status=stripe_status,
    )
    session.add(discrepancy)
    await session.flush()
    return ReconciliationDiscrepancyDTO.model_validate(discrepancy)


async def list_discrepancies(
    session: AsyncSession,
    run_id: uuid.UUID | None = None,
    limit: int = 100,
    offset: int = 0,
) -> list[ReconciliationDiscrepancyDTO]:
    query = select(ReconciliationDiscrepancy).order_by(
        ReconciliationDiscrepancy.detected_at.desc()
    )
    if run_id is not None:
        query = query.where(ReconciliationDiscrepancy.run_id == run_id)
    query = query.limit(limit).offset(offset)
    result = await session.execute(query)
    return [
        ReconciliationDiscrepancyDTO.model_validate(row)
        for row in result.scalars().all()
    ]
