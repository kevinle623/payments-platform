"""
ACH processor adapter -- simulates bank-to-bank transfer lifecycle.

ACH differs from card networks in two key ways:
- No client_secret / frontend UI step; payment is direct debit
- Async settlement: initiated as PENDING, settles 1-3 days later via NACHA
  return file. In this dev environment, settlement is driven by the
  ach_settlement Celery job rather than a real NACHA file.

Routing: bills set PROCESSOR=ach in env; zero changes needed to bill service.
"""

import uuid

from shared.exceptions import ProcessorError
from shared.logger import get_logger
from shared.processors.base import (
    CaptureResult,
    PaymentIntent,
    PaymentStatus,
    ProcessorEvent,
    RefundResult,
)

logger = get_logger(__name__)


class ACHAdapter:
    async def create_payment_intent(
        self,
        amount: int,
        currency: str,
        metadata: dict,
    ) -> PaymentIntent:
        processor_id = f"ach_{uuid.uuid4().hex}"
        logger.info(
            "ACH transfer initiated | processor_id=%s amount=%d currency=%s",
            processor_id,
            amount,
            currency,
        )
        return PaymentIntent(
            processor_id=processor_id,
            client_secret="",  # no frontend payment step for ACH
            status=PaymentStatus.PENDING,
            amount=amount,
            currency=currency,
            metadata=metadata,
        )

    async def capture(
        self,
        processor_payment_id: str,
    ) -> CaptureResult:
        # ACH has no auth+capture split; this represents async settlement
        # Called by the ach_settlement job via handle_payment_succeeded()
        logger.info("ACH transfer settled | processor_id=%s", processor_payment_id)
        return CaptureResult(
            processor_id=processor_payment_id,
            status=PaymentStatus.SUCCEEDED,
            amount=0,  # caller resolves amount from the payment record
            currency="usd",
        )

    async def refund(
        self,
        processor_payment_id: str,
        amount: int,
    ) -> RefundResult:
        refund_id = f"ach_refund_{uuid.uuid4().hex}"
        logger.info(
            "ACH refund initiated | processor_id=%s refund_id=%s amount=%d",
            processor_payment_id,
            refund_id,
            amount,
        )
        return RefundResult(
            processor_id=processor_payment_id,
            refund_id=refund_id,
            amount=amount,
            currency="usd",
        )

    async def parse_webhook(
        self,
        payload: bytes,
        signature: str,
    ) -> ProcessorEvent:
        # ACH settlement is driven by the ach_settlement Celery job, not webhooks
        raise ProcessorError(
            "ACH does not use webhooks; settlement is handled by the ach_settlement job"
        )
