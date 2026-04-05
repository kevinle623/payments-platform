import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.bills import service
from app.bills.models import BillStatus
from app.bills.schemas import (
    BillDetailResponse,
    BillDTO,
    BillExecutionResponse,
    CreateBillRequest,
    UpdateBillRequest,
)
from shared.db import get_db
from shared.logger import get_logger

router = APIRouter(prefix="/bills", tags=["bills"])
logger = get_logger(__name__)


@router.post("", response_model=BillDTO, status_code=201)
async def create_bill(
    request: CreateBillRequest,
    session: AsyncSession = Depends(get_db),
):
    logger.info(
        "create bill request received | payee_id=%s amount=%d frequency=%s",
        request.payee_id,
        request.amount,
        request.frequency,
    )
    return await service.create_bill(
        session=session,
        payee_id=request.payee_id,
        card_id=request.card_id,
        amount=request.amount,
        currency=request.currency,
        frequency=request.frequency,
        next_due_date=request.next_due_date,
    )


@router.get("", response_model=list[BillDTO])
async def list_bills(
    status: BillStatus | None = Query(default=None),
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    session: AsyncSession = Depends(get_db),
):
    logger.info(
        "list bills request received | status=%s limit=%d offset=%d",
        status,
        limit,
        offset,
    )
    return await service.list_bills(
        session=session,
        status=status,
        limit=limit,
        offset=offset,
    )


@router.get("/{bill_id}", response_model=BillDetailResponse)
async def get_bill(
    bill_id: uuid.UUID,
    session: AsyncSession = Depends(get_db),
):
    logger.info("get bill request received | bill_id=%s", bill_id)
    return await service.get_bill_detail(session=session, bill_id=bill_id)


@router.post("/{bill_id}/execute", response_model=BillExecutionResponse)
async def execute_bill(
    bill_id: uuid.UUID,
    session: AsyncSession = Depends(get_db),
):
    logger.info("execute bill request received | bill_id=%s trigger=manual", bill_id)
    return await service.execute_bill(
        session=session,
        bill_id=bill_id,
        trigger="manual",
    )


@router.patch("/{bill_id}", response_model=BillDTO)
async def update_bill(
    bill_id: uuid.UUID,
    request: UpdateBillRequest,
    session: AsyncSession = Depends(get_db),
):
    updates = {field: getattr(request, field) for field in request.model_fields_set}
    logger.info(
        "update bill request received | bill_id=%s updates=%s",
        bill_id,
        updates,
    )
    return await service.update_bill(
        session=session,
        bill_id=bill_id,
        updates=updates,
    )
