import asyncio
from datetime import datetime, timedelta, timezone

import stripe
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.payments import repository
from shared.logger import get_logger
from shared.settings import DATABASE_URL, STRIPE_SECRET_KEY
from workers.celery_app import celery_app

logger = get_logger(__name__)

_WINDOW_HOURS = 24

# Stripe status that corresponds to our SUCCEEDED status
_STRIPE_SETTLED_STATUS = "succeeded"


@celery_app.task(name="workers.jobs.payments.reconciliation.run_reconciliation")
def run_reconciliation() -> None:
    asyncio.run(_run())


async def _run() -> None:
    since = datetime.now(timezone.utc) - timedelta(hours=_WINDOW_HOURS)
    logger.info(
        "reconciliation started | window_hours=%d since=%s", _WINDOW_HOURS, since
    )

    engine = create_async_engine(DATABASE_URL)
    async_session = async_sessionmaker(engine, expire_on_commit=False)

    try:
        async with async_session() as session:
            payments = await repository.get_settled_since(session, since)

        if not payments:
            logger.info("reconciliation: no settled payments in window")
            return

        logger.info(
            "reconciliation: checking %d payments against Stripe", len(payments)
        )

        stripe.api_key = STRIPE_SECRET_KEY

        mismatches = 0
        for payment in payments:
            mismatch = await _check_payment(payment.processor_payment_id, payment.id)
            if mismatch:
                mismatches += 1

        logger.info(
            "reconciliation complete | checked=%d mismatches=%d",
            len(payments),
            mismatches,
        )
    finally:
        await engine.dispose()


async def _check_payment(processor_payment_id: str, payment_id) -> bool:
    try:
        intent = stripe.PaymentIntent.retrieve(processor_payment_id)
        if intent.status != _STRIPE_SETTLED_STATUS:
            logger.warning(
                "reconciliation mismatch | payment_id=%s processor_payment_id=%s "
                "our_status=succeeded stripe_status=%s",
                payment_id,
                processor_payment_id,
                intent.status,
            )
            return True
        return False
    except stripe.StripeError:
        logger.exception(
            "reconciliation stripe lookup failed | payment_id=%s processor_payment_id=%s",
            payment_id,
            processor_payment_id,
        )
        return True
