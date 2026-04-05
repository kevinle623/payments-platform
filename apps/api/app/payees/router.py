import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.payees import service
from app.payees.schemas import CreatePayeeRequest, PayeeDTO
from shared.db import get_db
from shared.logger import get_logger

router = APIRouter(prefix="/payees", tags=["payees"])
logger = get_logger(__name__)


@router.post("", response_model=PayeeDTO, status_code=201)
async def create_payee(
    request: CreatePayeeRequest,
    session: AsyncSession = Depends(get_db),
):
    logger.info(
        "create payee request received | name=%s payee_type=%s",
        request.name,
        request.payee_type,
    )
    return await service.create_payee(
        session=session,
        name=request.name,
        payee_type=request.payee_type,
        account_number=request.account_number,
        routing_number=request.routing_number,
        currency=request.currency,
    )


@router.get("", response_model=list[PayeeDTO])
async def list_payees(
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    session: AsyncSession = Depends(get_db),
):
    logger.info("list payees request received | limit=%d offset=%d", limit, offset)
    return await service.list_payees(session=session, limit=limit, offset=offset)


@router.get("/{payee_id}", response_model=PayeeDTO)
async def get_payee(
    payee_id: uuid.UUID,
    session: AsyncSession = Depends(get_db),
):
    logger.info("get payee request received | payee_id=%s", payee_id)
    return await service.get_payee(session=session, payee_id=payee_id)
