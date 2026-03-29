from dataclasses import dataclass
from enum import StrEnum
from typing import Protocol


class PaymentStatus(StrEnum):
    PENDING = "pending"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    REFUNDED = "refunded"
    DISPUTED = "disputed"


class ProcessorEventType(StrEnum):
    PAYMENT_SUCCEEDED = "payment.succeeded"
    PAYMENT_FAILED = "payment.failed"
    PAYMENT_REFUNDED = "payment.refunded"
    DISPUTE_CREATED = "dispute.created"


# normalized internal DTOs -- every adapter maps its processor-specific
# response shapes into these types. Nothing outside shared/processors
# ever sees raw Stripe or Braintree objects.


@dataclass
class PaymentIntent:
    processor_id: str
    status: PaymentStatus
    amount: int  # always in cents
    currency: str
    metadata: dict


@dataclass
class CaptureResult:
    processor_id: str
    status: PaymentStatus
    amount: int
    currency: str


@dataclass
class RefundResult:
    processor_id: str
    refund_id: str
    amount: int
    currency: str


@dataclass
class ProcessorEvent:
    event_type: ProcessorEventType
    processor_payment_id: str
    amount: int
    currency: str
    metadata: dict


class PaymentProcessor(Protocol):
    async def create_payment_intent(
        self,
        amount: int,
        currency: str,
        metadata: dict,
    ) -> PaymentIntent: ...

    async def capture(
        self,
        processor_payment_id: str,
    ) -> CaptureResult: ...

    async def refund(
        self,
        processor_payment_id: str,
        amount: int,
    ) -> RefundResult: ...

    async def parse_webhook(
        self,
        payload: bytes,
        signature: str,
    ) -> ProcessorEvent: ...
