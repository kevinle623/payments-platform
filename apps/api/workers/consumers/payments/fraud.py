"""
Fraud consumer -- subscribes to payment.authorized events and scores the payment.

Routing keys: payment.authorized
Queue: payments.fraud

Scores payments by amount, persists a FraudSignal row for each event.
High-value payments (>= $100) are flagged as high risk.
"""

import uuid

from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.fraud import service as fraud_service
from app.fraud.models import RiskLevel
from shared.logger import get_logger
from shared.settings import DATABASE_URL
from workers.consumers.base import start
from workers.exchanges import PAYMENTS_EXCHANGE

logger = get_logger(__name__)

_QUEUE_NAME = "payments.fraud"
_ROUTING_KEYS = ["payment.authorized"]

_HIGH_VALUE_THRESHOLD = 10_000  # cents ($100)


async def _handle(event_type: str, payload: dict) -> None:
    payment_id_raw = payload.get("payment_id")
    amount = payload.get("amount", 0)
    currency = payload.get("currency", "usd")

    if payment_id_raw is None:
        logger.warning("fraud consumer received event with no payment_id, skipping")
        return

    payment_id = uuid.UUID(str(payment_id_raw))
    risk_level = RiskLevel.HIGH if amount >= _HIGH_VALUE_THRESHOLD else RiskLevel.LOW

    engine = create_async_engine(DATABASE_URL)
    try:
        async_session = async_sessionmaker(engine, expire_on_commit=False)
        async with async_session() as session:
            signal = await fraud_service.create_signal(
                session=session,
                payment_id=payment_id,
                risk_level=risk_level,
                amount=amount,
                currency=currency,
            )
        logger.info(
            "fraud signal persisted | signal_id=%s payment_id=%s risk=%s amount=%d currency=%s",
            signal.id,
            payment_id,
            risk_level,
            amount,
            currency,
        )
        if risk_level == RiskLevel.HIGH:
            logger.warning(
                "high-value payment flagged | payment_id=%s amount=%d",
                payment_id,
                amount,
            )
    finally:
        await engine.dispose()


if __name__ == "__main__":
    start(PAYMENTS_EXCHANGE, _QUEUE_NAME, _ROUTING_KEYS, _handle)
