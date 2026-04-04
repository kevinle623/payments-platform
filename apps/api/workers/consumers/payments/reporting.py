"""
Reporting consumer -- records all payment lifecycle events for analytics.

Routing keys: payment.authorized, payment.settled, payment.refunded
Queue: payments.reporting

Writes a ReportingEvent row per message so the summary endpoint can
aggregate daily volume by event type and currency.
"""

import uuid

from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.reporting import service as reporting_service
from shared.logger import get_logger
from shared.settings import DATABASE_URL
from workers.consumers.base import start
from workers.exchanges import PAYMENTS_EXCHANGE

logger = get_logger(__name__)

_QUEUE_NAME = "payments.reporting"
_ROUTING_KEYS = ["payment.authorized", "payment.settled", "payment.refunded"]


async def _handle(event_type: str, payload: dict) -> None:
    payment_id_raw = payload.get("payment_id")
    amount = payload.get("amount", 0)
    currency = (payload.get("currency") or "usd").lower()

    if payment_id_raw is None:
        logger.warning("reporting consumer received event with no payment_id, skipping")
        return

    payment_id = uuid.UUID(str(payment_id_raw))

    engine = create_async_engine(DATABASE_URL)
    try:
        async_session = async_sessionmaker(engine, expire_on_commit=False)
        async with async_session() as session:
            event = await reporting_service.record_event(
                session=session,
                event_type=event_type,
                payment_id=payment_id,
                amount=amount,
                currency=currency,
            )
        logger.info(
            "reporting event persisted | event_id=%s event_type=%s payment_id=%s amount=%d currency=%s",
            event.id,
            event_type,
            payment_id,
            amount,
            currency,
        )
    finally:
        await engine.dispose()


if __name__ == "__main__":
    start(PAYMENTS_EXCHANGE, _QUEUE_NAME, _ROUTING_KEYS, _handle)
