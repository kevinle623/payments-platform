"""
Fraud consumer -- subscribes to payment.authorized events and scores the payment.

Routing keys: payment.authorized
Queue: payments.fraud

In production this would call a risk model or rules engine.
For now it logs the signal and flags high-value payments.
"""

from shared.logger import get_logger
from workers.consumers.base import start
from workers.exchanges import PAYMENTS_EXCHANGE

logger = get_logger(__name__)

_QUEUE_NAME = "payments.fraud"
_ROUTING_KEYS = ["payment.authorized"]

_HIGH_VALUE_THRESHOLD = 10_000  # cents


async def _handle(event_type: str, payload: dict) -> None:
    payment_id = payload.get("payment_id")
    amount = payload.get("amount", 0)
    currency = payload.get("currency")

    risk_signal = "high" if amount >= _HIGH_VALUE_THRESHOLD else "low"

    logger.info(
        "fraud score | payment_id=%s amount=%d currency=%s risk=%s",
        payment_id,
        amount,
        currency,
        risk_signal,
    )

    if risk_signal == "high":
        logger.warning(
            "high-value payment flagged for review | payment_id=%s amount=%d",
            payment_id,
            amount,
        )


if __name__ == "__main__":
    start(PAYMENTS_EXCHANGE, _QUEUE_NAME, _ROUTING_KEYS, _handle)
