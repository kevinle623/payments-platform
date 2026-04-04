from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.fraud import service
from app.fraud.models import RiskLevel
from app.fraud.schemas import FraudSignalDTO
from shared.db import get_db
from shared.logger import get_logger

router = APIRouter(prefix="/fraud", tags=["fraud"])
logger = get_logger(__name__)


@router.get("/signals", response_model=list[FraudSignalDTO])
async def list_signals(
    risk_level: RiskLevel | None = Query(default=None),
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    session: AsyncSession = Depends(get_db),
):
    logger.info(
        "list fraud signals | risk_level=%s limit=%d offset=%d",
        risk_level,
        limit,
        offset,
    )
    return await service.list_signals(
        session=session,
        risk_level=risk_level,
        limit=limit,
        offset=offset,
    )
