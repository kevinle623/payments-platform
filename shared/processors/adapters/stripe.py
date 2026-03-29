import stripe

from shared.exceptions import ProcessorError
from shared.logger import logger
from shared.processors.base import (
    CaptureResult,
    PaymentIntent,
    PaymentStatus,
    ProcessorEvent,
    ProcessorEventType,
    RefundResult,
)
from shared.settings import STRIPE_SECRET_KEY, STRIPE_WEBHOOK_SECRET

stripe.api_key = STRIPE_SECRET_KEY

_STATUS_MAP = {
    "requires_capture": PaymentStatus.PENDING,
    "succeeded": PaymentStatus.SUCCEEDED,
    "canceled": PaymentStatus.FAILED,
    "requires_payment_method": PaymentStatus.FAILED,
}

_EVENT_MAP = {
    "payment_intent.succeeded": ProcessorEventType.PAYMENT_SUCCEEDED,
    "payment_intent.payment_failed": ProcessorEventType.PAYMENT_FAILED,
    "charge.refunded": ProcessorEventType.PAYMENT_REFUNDED,
    "charge.dispute.created": ProcessorEventType.DISPUTE_CREATED,
}


class StripeAdapter:
    # noinspection PyMethodMayBeStatic
    async def create_payment_intent(
        self,
        amount: int,
        currency: str,
        metadata: dict,
    ) -> PaymentIntent:
        try:
            intent = stripe.PaymentIntent.create(
                amount=amount,
                currency=currency,
                capture_method="manual",  # authorize now, capture separately
                metadata=metadata,
            )
            return PaymentIntent(
                processor_id=intent.id,
                status=_STATUS_MAP.get(intent.status, PaymentStatus.PENDING),
                amount=intent.amount,
                currency=intent.currency,
                metadata=intent.metadata._to_dict_recursive(),
            )
        except stripe.StripeError as e:
            raise ProcessorError(str(e)) from e

    # noinspection PyMethodMayBeStatic
    async def capture(
        self,
        processor_payment_id: str,
    ) -> CaptureResult:
        try:
            intent = stripe.PaymentIntent.capture(processor_payment_id)
            return CaptureResult(
                processor_id=intent.id,
                status=_STATUS_MAP.get(intent.status, PaymentStatus.SUCCEEDED),
                amount=intent.amount_received,
                currency=intent.currency,
            )
        except stripe.StripeError as e:
            raise ProcessorError(str(e)) from e

    # noinspection PyMethodMayBeStatic
    async def refund(
        self,
        processor_payment_id: str,
        amount: int,
    ) -> RefundResult:
        try:
            refund = stripe.Refund.create(
                payment_intent=processor_payment_id,
                amount=amount,
            )
            return RefundResult(
                processor_id=processor_payment_id,
                refund_id=refund.id,
                amount=refund.amount,
                currency=refund.currency,
            )
        except stripe.StripeError as e:
            raise ProcessorError(str(e)) from e

    # noinspection PyMethodMayBeStatic
    async def parse_webhook(self, payload: bytes, signature: str) -> ProcessorEvent:
        try:
            event = stripe.Webhook.construct_event(
                payload, signature, STRIPE_WEBHOOK_SECRET
            )
        except stripe.SignatureVerificationError as e:
            raise ProcessorError("Invalid webhook signature") from e

        logger.info("Received Stripe event: %s", event.type)
        logger.info("Raw event object: %s", event.data.object)

        event_type = _EVENT_MAP.get(event.type)
        if not event_type:
            logger.info("Ignoring unhandled event type: %s", event.type)
            return None

        obj_dict = event.data.object._to_dict_recursive()
        logger.info("Converted to dict: %s", obj_dict)

        return ProcessorEvent(
            event_type=event_type,
            processor_payment_id=obj_dict.get("id") or obj_dict.get("payment_intent"),
            amount=obj_dict.get("amount", 0),
            currency=obj_dict.get("currency", "usd"),
            metadata=obj_dict.get("metadata", {}),
        )
