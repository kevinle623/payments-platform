import asyncio
import uuid
from datetime import datetime, timedelta, timezone

import stripe
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.outbox import service as outbox_service
from app.outbox.models import OutboxEventType
from app.payments import repository as payments_repository
from app.reconciliation import repository as reconciliation_repository
from shared.logger import get_logger
from shared.settings import DATABASE_URL, STRIPE_SECRET_KEY
from workers.celery_app import celery_app

logger = get_logger(__name__)

_WINDOW_HOURS = 24
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
            run = await reconciliation_repository.create_run(session)
            logger.info("reconciliation run created | run_id=%s", run.id)

            payments = await payments_repository.get_settled_since(session, since)

            if not payments:
                logger.info("reconciliation: no settled payments in window")
                await reconciliation_repository.complete_run(
                    session, run.id, checked=0, mismatches=0
                )
                await session.commit()
                return

            logger.info(
                "reconciliation: checking %d payments against Stripe", len(payments)
            )

            stripe.api_key = STRIPE_SECRET_KEY
            mismatch_count = 0

            for payment in payments:
                is_mismatch = await _check_payment(session, run.id, payment)
                if is_mismatch:
                    mismatch_count += 1

            await reconciliation_repository.complete_run(
                session,
                run.id,
                checked=len(payments),
                mismatches=mismatch_count,
            )
            await session.commit()

            logger.info(
                "reconciliation complete | run_id=%s checked=%d mismatches=%d",
                run.id,
                len(payments),
                mismatch_count,
            )
    finally:
        await engine.dispose()


async def _check_payment(
    session: AsyncSession,
    run_id: uuid.UUID,
    payment,
) -> bool:
    """
    Check a single payment against Stripe. Returns True if a mismatch is found.
    Writes a ReconciliationDiscrepancy row and publishes an outbox event on mismatch.
    """
    try:
        intent = stripe.PaymentIntent.retrieve(payment.processor_payment_id)
        stripe_status = intent.status

        if stripe_status == _STRIPE_SETTLED_STATUS:
            return False

        logger.warning(
            "reconciliation mismatch | payment_id=%s processor_payment_id=%s "
            "our_status=succeeded stripe_status=%s",
            payment.id,
            payment.processor_payment_id,
            stripe_status,
        )

    except stripe.StripeError:
        logger.exception(
            "reconciliation stripe lookup failed | payment_id=%s processor_payment_id=%s",
            payment.id,
            payment.processor_payment_id,
        )
        stripe_status = "unknown"

    # write discrepancy row
    discrepancy = await reconciliation_repository.create_discrepancy(
        session,
        run_id=run_id,
        payment_id=payment.id,
        processor_payment_id=payment.processor_payment_id,
        our_status="succeeded",
        stripe_status=stripe_status,
    )

    # publish outbox event so the notifications consumer can alert
    await outbox_service.publish_event(
        session,
        event_type=OutboxEventType.RECONCILIATION_MISMATCH,
        payload={
            "run_id": str(run_id),
            "discrepancy_id": str(discrepancy.id),
            "payment_id": str(payment.id),
            "processor_payment_id": payment.processor_payment_id,
            "our_status": "succeeded",
            "stripe_status": stripe_status,
        },
    )

    return True
