import asyncio
from datetime import datetime, timedelta, timezone

from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.issuer.auth import repository as auth_repository
from app.issuer.settlement import service as issuer_settlement_service
from app.payments import repository as payments_repository
from shared.logger import get_logger
from shared.processors.base import PaymentStatus
from shared.settings import DATABASE_URL
from workers.celery_app import celery_app

logger = get_logger(__name__)

_HOLD_EXPIRY_DAYS = 7


@celery_app.task(name="workers.jobs.issuer.hold_expiry.run_hold_expiry")
def run_hold_expiry() -> None:
    asyncio.run(_run())


async def _run() -> None:
    expiry_cutoff = datetime.now(timezone.utc) - timedelta(days=_HOLD_EXPIRY_DAYS)
    logger.info("hold expiry started | expiry_cutoff=%s", expiry_cutoff)

    engine = create_async_engine(DATABASE_URL)
    async_session = async_sessionmaker(engine, expire_on_commit=False)

    try:
        async with async_session() as session:
            stale_auths = await auth_repository.get_stale_approved(
                session, older_than=expiry_cutoff
            )

            if not stale_auths:
                logger.info("hold expiry: no stale approved holds found")
                return

            logger.info("hold expiry: found %d stale holds", len(stale_auths))

            expired_count = 0
            cleared_count = 0

            for auth in stale_auths:
                payment = await payments_repository.get_by_idempotency_key(
                    session, auth.idempotency_key
                )

                if payment and payment.status in (
                    PaymentStatus.SUCCEEDED,
                    PaymentStatus.REFUNDED,
                ):
                    # hold was already cleared during settlement -- just mark expired
                    await auth_repository.mark_expired(session, auth.id)
                    logger.info(
                        "hold expiry: auth already settled, marking expired | authorization_id=%s",
                        auth.id,
                    )
                else:
                    # genuinely stale hold -- clear ledger entries then mark expired
                    await issuer_settlement_service.clear_hold(
                        session, auth.idempotency_key, auth.amount
                    )
                    await auth_repository.mark_expired(session, auth.id)
                    cleared_count += 1
                    logger.info(
                        "hold expiry: stale hold cleared and expired | authorization_id=%s card_id=%s amount=%d",
                        auth.id,
                        auth.card_id,
                        auth.amount,
                    )

                expired_count += 1

            await session.commit()
            logger.info(
                "hold expiry complete | expired=%d cleared=%d",
                expired_count,
                cleared_count,
            )
    finally:
        await engine.dispose()
