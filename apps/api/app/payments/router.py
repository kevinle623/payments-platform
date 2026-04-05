import uuid

from fastapi import APIRouter, Depends, Header, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.payments import service
from app.payments.schemas import (
    AuthorizeRequest,
    AuthorizeResponse,
    CaptureRequest,
    CaptureResponse,
    PaymentDetailResponse,
    PaymentRecord,
    RefundRequest,
    RefundResponse,
)
from shared.db import get_db
from shared.logger import get_logger
from shared.processors.base import PaymentStatus, ProcessorEventType
from shared.processors.factory import get_processor
from shared.settings import CASH_ACCOUNT_ID, EXPENSE_ACCOUNT_ID, LIABILITY_ACCOUNT_ID

router = APIRouter(prefix="/payments", tags=["payments"])
logger = get_logger(__name__)


@router.get("", response_model=list[PaymentRecord])
async def list_payments(
    status: PaymentStatus | None = Query(default=None),
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    session: AsyncSession = Depends(get_db),
):
    logger.info(
        "list payments request received | status=%s limit=%d offset=%d",
        status,
        limit,
        offset,
    )
    return await service.list_payments(
        session=session,
        status=status,
        limit=limit,
        offset=offset,
    )


@router.get("/{payment_id}", response_model=PaymentDetailResponse)
async def get_payment(
    payment_id: uuid.UUID,
    session: AsyncSession = Depends(get_db),
):
    logger.info("get payment detail request received | payment_id=%s", payment_id)
    return await service.get_payment_detail(session=session, payment_id=payment_id)


@router.post("/authorize", response_model=AuthorizeResponse)
async def authorize(
    request: AuthorizeRequest,
    session: AsyncSession = Depends(get_db),
):
    logger.info(
        "authorize request received | idempotency_key=%s amount=%d currency=%s",
        request.idempotency_key,
        request.amount,
        request.currency,
    )
    processor = get_processor()
    return await service.authorize(
        session=session,
        request=request,
        processor=processor,
        expense_account_id=uuid.UUID(EXPENSE_ACCOUNT_ID),
        liability_account_id=uuid.UUID(LIABILITY_ACCOUNT_ID),
    )


@router.post("/capture", response_model=CaptureResponse)
async def capture(
    request: CaptureRequest,
    session: AsyncSession = Depends(get_db),
):
    logger.info(
        "capture request received | processor_payment_id=%s",
        request.processor_payment_id,
    )
    processor = get_processor()
    return await service.capture(
        session=session,
        processor_payment_id=request.processor_payment_id,
        processor=processor,
        liability_account_id=uuid.UUID(LIABILITY_ACCOUNT_ID),
        cash_account_id=uuid.UUID(CASH_ACCOUNT_ID),
    )


@router.post("/refund", response_model=RefundResponse)
async def refund(
    request: RefundRequest,
    session: AsyncSession = Depends(get_db),
):
    logger.info(
        "refund request received | processor_payment_id=%s amount=%d",
        request.processor_payment_id,
        request.amount,
    )
    processor = get_processor()
    return await service.refund(
        session=session,
        processor_payment_id=request.processor_payment_id,
        amount=request.amount,
        processor=processor,
    )


@router.post("/webhooks/stripe")
async def stripe_webhook(
    request: Request,
    stripe_signature: str = Header(alias="stripe-signature"),
    session: AsyncSession = Depends(get_db),
):
    payload = await request.body()
    processor = get_processor()
    event = await processor.parse_webhook(payload, stripe_signature)

    if event is None:
        logger.info("stripe webhook received | event ignored (unhandled type)")
        return {"status": "ignored"}

    logger.info(
        "stripe webhook received | event_type=%s processor_payment_id=%s",
        event.event_type,
        event.processor_payment_id,
    )

    if event.event_type == ProcessorEventType.PAYMENT_SUCCEEDED:
        # don't call processor.capture() -- money already moved
        # just update our internal records
        await service.handle_payment_succeeded(
            session=session,
            processor_payment_id=event.processor_payment_id,
            liability_account_id=uuid.UUID(LIABILITY_ACCOUNT_ID),
            cash_account_id=uuid.UUID(CASH_ACCOUNT_ID),
        )
    elif event.event_type == ProcessorEventType.PAYMENT_REFUNDED:
        await service.handle_payment_refunded(
            session=session, processor_payment_id=event.processor_payment_id
        )

    return {"status": "accepted"}
