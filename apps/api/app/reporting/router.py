from datetime import datetime

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.reporting import service
from app.reporting.schemas import ReportingSummaryEntry
from shared.db import get_db
from shared.logger import get_logger

router = APIRouter(prefix="/reporting", tags=["reporting"])
logger = get_logger(__name__)


@router.get("/summary", response_model=list[ReportingSummaryEntry])
async def get_summary(
    since: datetime | None = Query(default=None),
    until: datetime | None = Query(default=None),
    session: AsyncSession = Depends(get_db),
):
    logger.info("reporting summary requested | since=%s until=%s", since, until)
    return await service.get_summary(session=session, since=since, until=until)
