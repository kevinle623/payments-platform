"""
Notifications consumer -- sends notifications for all payment lifecycle events.

Routing keys: payment.authorized, payment.settled, payment.refunded
Queue: payments.notifications

For each event:
  1. If card_id is in the payload, look up the card -> cardholder -> email
  2. Deliver via NotificationSender (SmtpSender or StubSender based on settings)
  3. Persist a NotificationLog row
"""

import uuid

from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.issuer.cards import repository as cards_repository
from app.notifications import service as notifications_service
from app.notifications.sender.factory import get_sender
from shared.logger import get_logger
from shared.settings import DATABASE_URL
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
    amount = payload.get("amount", 0)
    currency = (payload.get("currency") or "usd").upper()
    card_id_raw = payload.get("card_id")

    template = _MESSAGES.get(event_type)
    if not template:
        logger.warning("notifications: unhandled event_type=%s", event_type)
        return

    message = template.format(amount=amount, currency=currency)

    engine = create_async_engine(DATABASE_URL)
    try:
        async_session = async_sessionmaker(engine, expire_on_commit=False)
        async with async_session() as session:
            to_email: str | None = None
            cardholder_id: uuid.UUID | None = None

            if card_id_raw:
                card_id = uuid.UUID(str(card_id_raw))
                card = await cards_repository.get_card(session, card_id)
                if card:
                    cardholder = await cards_repository.get_cardholder(
                        session, card.cardholder_id
                    )
                    if cardholder:
                        to_email = cardholder.email
                        cardholder_id = cardholder.id
                        logger.info(
                            "notifications: resolved cardholder | card_id=%s cardholder_id=%s email=%s",
                            card_id,
                            cardholder_id,
                            to_email,
                        )
                    else:
                        logger.warning(
                            "notifications: cardholder not found | card_id=%s cardholder_id=%s",
                            card_id,
                            card.cardholder_id,
                        )
                else:
                    logger.warning(
                        "notifications: card not found | card_id=%s", card_id
                    )

            sender = get_sender()
            log = await notifications_service.send_and_log(
                session=session,
                sender=sender,
                event_type=event_type,
                message=message,
                to_email=to_email,
                cardholder_id=cardholder_id,
            )
            await session.commit()

        logger.info(
            "notification logged | log_id=%s event_type=%s cardholder_id=%s",
            log.id,
            event_type,
            cardholder_id,
        )
    finally:
        await engine.dispose()


if __name__ == "__main__":
    start(PAYMENTS_EXCHANGE, _QUEUE_NAME, _ROUTING_KEYS, _handle)
