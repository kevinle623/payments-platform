import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.reconciliation import repository
from app.reconciliation.schemas import (
    ReconciliationDiscrepancyDTO,
    ReconciliationRunDTO,
)


async def list_runs(
    session: AsyncSession,
    limit: int = 50,
    offset: int = 0,
) -> list[ReconciliationRunDTO]:
    return await repository.list_runs(session=session, limit=limit, offset=offset)


async def list_discrepancies(
    session: AsyncSession,
    run_id: uuid.UUID | None = None,
    limit: int = 100,
    offset: int = 0,
) -> list[ReconciliationDiscrepancyDTO]:
    return await repository.list_discrepancies(
        session=session,
        run_id=run_id,
        limit=limit,
        offset=offset,
    )
