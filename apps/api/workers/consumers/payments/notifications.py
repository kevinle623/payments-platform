"""
Notifications consumer -- sends notifications for payment and bill lifecycle
events, plus system alerts such as reconciliation mismatches.

Routing keys: payment.authorized, payment.settled, payment.refunded,
              bill.scheduled, bill.executed, bill.failed,
              reconciliation.mismatch
Queue: payments.notifications
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
_ROUTING_KEYS = [
    "payment.authorized",
    "payment.settled",
    "payment.refunded",
    "bill.scheduled",
    "bill.executed",
    "bill.failed",
    "reconciliation.mismatch",
]

_PAYMENT_MESSAGES = {
    "payment.authorized": "Your payment of {amount} {currency} has been authorized.",
    "payment.settled": "Your payment of {amount} {currency} has been completed.",
    "payment.refunded": "Your refund of {amount} {currency} is being processed.",
}

_BILL_MESSAGES = {
    "bill.scheduled": "Your bill of {amount} {currency} is scheduled for {next_due_date}.",
    "bill.executed": "Your bill of {amount} {currency} has been executed.",
    "bill.failed": "Your bill of {amount} {currency} failed. Reason: {error}.",
}


async def _handle(event_type: str, payload: dict) -> None:
    engine = create_async_engine(DATABASE_URL)
    try:
        async_session = async_sessionmaker(engine, expire_on_commit=False)
        async with async_session() as session:
            if event_type == "reconciliation.mismatch":
                await _handle_reconciliation_mismatch(session, payload)
            elif event_type in _PAYMENT_MESSAGES:
                await _handle_payment_event(session, event_type, payload)
            elif event_type in _BILL_MESSAGES:
                await _handle_bill_event(session, event_type, payload)
            else:
                logger.warning("notifications: unhandled event_type=%s", event_type)
                return
            await session.commit()
    finally:
        await engine.dispose()


async def _handle_payment_event(session, event_type: str, payload: dict) -> None:
    amount = payload.get("amount", 0)
    currency = (payload.get("currency") or "usd").upper()
    card_id_raw = payload.get("card_id")

    message = _PAYMENT_MESSAGES[event_type].format(amount=amount, currency=currency)

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
            logger.warning("notifications: card not found | card_id=%s", card_id)

    sender = get_sender()
    log = await notifications_service.send_and_log(
        session=session,
        sender=sender,
        event_type=event_type,
        message=message,
        to_email=to_email,
        cardholder_id=cardholder_id,
    )
    logger.info(
        "notification logged | log_id=%s event_type=%s cardholder_id=%s",
        log.id,
        event_type,
        cardholder_id,
    )


async def _handle_reconciliation_mismatch(session, payload: dict) -> None:
    payment_id = payload.get("payment_id")
    our_status = payload.get("our_status")
    stripe_status = payload.get("stripe_status")
    run_id = payload.get("run_id")

    message = (
        f"Reconciliation mismatch detected | run_id={run_id} "
        f"payment_id={payment_id} our_status={our_status} stripe_status={stripe_status}"
    )

    logger.warning(message)

    # system alert -- no cardholder, no email delivery
    # persisted so the alert is queryable via notification_logs
    sender = get_sender()
    log = await notifications_service.send_and_log(
        session=session,
        sender=sender,
        event_type="reconciliation.mismatch",
        message=message,
        to_email=None,
        cardholder_id=None,
    )
    logger.info(
        "reconciliation mismatch alert logged | log_id=%s payment_id=%s",
        log.id,
        payment_id,
    )


async def _handle_bill_event(session, event_type: str, payload: dict) -> None:
    amount = payload.get("amount", 0)
    currency = (payload.get("currency") or "usd").upper()
    error = payload.get("error") or "unknown"
    next_due_date = payload.get("next_due_date") or "unspecified date"
    card_id_raw = payload.get("card_id")

    message = _BILL_MESSAGES[event_type].format(
        amount=amount,
        currency=currency,
        error=error,
        next_due_date=next_due_date,
    )

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

    sender = get_sender()
    log = await notifications_service.send_and_log(
        session=session,
        sender=sender,
        event_type=event_type,
        message=message,
        to_email=to_email,
        cardholder_id=cardholder_id,
    )
    logger.info(
        "bill notification logged | log_id=%s event_type=%s cardholder_id=%s",
        log.id,
        event_type,
        cardholder_id,
    )


if __name__ == "__main__":
    start(PAYMENTS_EXCHANGE, _QUEUE_NAME, _ROUTING_KEYS, _handle)
