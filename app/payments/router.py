import uuid

from fastapi import APIRouter, Depends, Header, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.payments import service
from app.payments.schemas import (
    AuthorizeRequest,
    AuthorizeResponse,
    CaptureRequest,
    CaptureResponse,
    RefundRequest,
    RefundResponse,
)
from shared.db import get_db
from shared.processors.base import ProcessorEventType
from shared.processors.factory import get_processor
from shared.settings import CASH_ACCOUNT_ID, EXPENSE_ACCOUNT_ID, LIABILITY_ACCOUNT_ID

router = APIRouter(prefix="/payments", tags=["payments"])


@router.post("/authorize", response_model=AuthorizeResponse)
async def authorize(
    request: AuthorizeRequest,
    session: AsyncSession = Depends(get_db),
):
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

    # dispatch based on event type
    if event.event_type == ProcessorEventType.PAYMENT_SUCCEEDED:
        await service.capture(
            session=session,
            processor_payment_id=event.processor_payment_id,
            processor=processor,
            liability_account_id=uuid.UUID(LIABILITY_ACCOUNT_ID),
            cash_account_id=uuid.UUID(CASH_ACCOUNT_ID),
        )
    elif event.event_type == ProcessorEventType.PAYMENT_REFUNDED:
        await service.refund(
            session=session,
            processor_payment_id=event.processor_payment_id,
            amount=event.amount,
            processor=processor,
        )

    # always return 200 fast -- Stripe will retry if we don't
    return {"status": "accepted"}
