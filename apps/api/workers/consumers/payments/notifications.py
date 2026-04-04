"""
Notifications consumer -- sends simulated notifications for all payment lifecycle events.

Routing keys: payment.authorized, payment.settled, payment.refunded
Queue: payments.notifications

In production this would call an email/SMS/push provider.
For now it logs the notification that would be sent.
"""

from shared.logger import get_logger
from workers.consumers.base import start
from workers.exchanges import PAYMENTS_EXCHANGE

logger = get_logger(__name__)

_QUEUE_NAME = "payments.notifications"
_ROUTING_KEYS = ["payment.authorized", "payment.settled", "payment.refunded"]

_MESSAGES = {
    "payment.authorized": "Your payment of {amount} {currency} has been authorized.",
    "payment.settled": "Your payment of {amount} {currency} has been completed.",
    "payment.refunded": "Your refund of {amount} {currency} is being processed.",
}


async def _handle(event_type: str, payload: dict) -> None:
    payment_id = payload.get("payment_id")
    amount = payload.get("amount", 0)
    currency = (payload.get("currency") or "").upper()

    template = _MESSAGES.get(event_type)
    if not template:
        logger.warning("notifications: unhandled event_type=%s", event_type)
        return

    message = template.format(amount=amount, currency=currency)
    logger.info(
        "notification sent | payment_id=%s event_type=%s message=%r",
        payment_id,
        event_type,
        message,
    )


if __name__ == "__main__":
    start(PAYMENTS_EXCHANGE, _QUEUE_NAME, _ROUTING_KEYS, _handle)
