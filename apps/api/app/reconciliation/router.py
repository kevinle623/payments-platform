import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.reconciliation import service
from app.reconciliation.schemas import ReconciliationDiscrepancyDTO, ReconciliationRunDTO
from shared.db import get_db
from shared.logger import get_logger

router = APIRouter(prefix="/reconciliation", tags=["reconciliation"])
logger = get_logger(__name__)


@router.get("/runs", response_model=list[ReconciliationRunDTO])
async def list_runs(
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    session: AsyncSession = Depends(get_db),
):
    logger.info("list reconciliation runs | limit=%d offset=%d", limit, offset)
    return await service.list_runs(session=session, limit=limit, offset=offset)


@router.get("/discrepancies", response_model=list[ReconciliationDiscrepancyDTO])
async def list_discrepancies(
    run_id: uuid.UUID | None = Query(default=None),
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    session: AsyncSession = Depends(get_db),
):
    logger.info(
        "list reconciliation discrepancies | run_id=%s limit=%d offset=%d",
        run_id,
        limit,
        offset,
    )
    return await service.list_discrepancies(
        session=session, run_id=run_id, limit=limit, offset=offset
    )
