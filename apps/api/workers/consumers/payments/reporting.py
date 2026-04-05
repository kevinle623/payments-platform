"""
Reporting consumer -- records payment and bill lifecycle events for analytics.

Routing keys: payment.authorized, payment.settled, payment.refunded,
              bill.scheduled, bill.executed, bill.failed
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
_ROUTING_KEYS = [
    "payment.authorized",
    "payment.settled",
    "payment.refunded",
    "bill.scheduled",
    "bill.executed",
    "bill.failed",
]


async def _handle(event_type: str, payload: dict) -> None:
    entity_id = _resolve_entity_id(event_type, payload)
    amount = payload.get("amount", 0)
    currency = (payload.get("currency") or "usd").lower()

    if entity_id is None:
        logger.warning(
            "reporting consumer received event with no payment_id/bill_id, skipping"
        )
        return

    engine = create_async_engine(DATABASE_URL)
    try:
        async_session = async_sessionmaker(engine, expire_on_commit=False)
        async with async_session() as session:
            event = await reporting_service.record_event(
                session=session,
                event_type=event_type,
                payment_id=entity_id,
                amount=amount,
                currency=currency,
            )
        logger.info(
            "reporting event persisted | event_id=%s event_type=%s entity_id=%s amount=%d currency=%s",
            event.id,
            event_type,
            entity_id,
            amount,
            currency,
        )
    finally:
        await engine.dispose()


def _resolve_entity_id(event_type: str, payload: dict) -> uuid.UUID | None:
    payment_id_raw = payload.get("payment_id")
    if payment_id_raw:
        return uuid.UUID(str(payment_id_raw))

    bill_id_raw = payload.get("bill_id")
    if not bill_id_raw:
        return None

    # reporting_events requires a UUID id; for bill events without payment_id
    # use a deterministic synthetic UUID derived from bill_id + event_type.
    return uuid.uuid5(uuid.NAMESPACE_URL, f"bill:{bill_id_raw}:{event_type}")


if __name__ == "__main__":
    start(PAYMENTS_EXCHANGE, _QUEUE_NAME, _ROUTING_KEYS, _handle)
