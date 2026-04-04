"""
Reporting consumer -- records all payment lifecycle events for analytics/reporting.

Routing keys: payment.authorized, payment.settled, payment.refunded
Queue: payments.reporting

In production this would write to a data warehouse or analytics pipeline.
For now it logs the reporting entry that would be emitted.
"""

from shared.logger import get_logger
from workers.consumers.base import start
from workers.exchanges import PAYMENTS_EXCHANGE

logger = get_logger(__name__)

_QUEUE_NAME = "payments.reporting"
_ROUTING_KEYS = ["payment.authorized", "payment.settled", "payment.refunded"]


async def _handle(event_type: str, payload: dict) -> None:
    payment_id = payload.get("payment_id")
    processor_payment_id = payload.get("processor_payment_id")
    amount = payload.get("amount", 0)
    currency = payload.get("currency")

    logger.info(
        "reporting entry | event_type=%s payment_id=%s processor_payment_id=%s amount=%d currency=%s",
        event_type,
        payment_id,
        processor_payment_id,
        amount,
        currency,
    )


if __name__ == "__main__":
    start(PAYMENTS_EXCHANGE, _QUEUE_NAME, _ROUTING_KEYS, _handle)
