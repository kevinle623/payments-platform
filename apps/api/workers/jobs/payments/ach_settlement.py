"""
ACH settlement job -- simulates async NACHA settlement for pending ACH payments.

In production, ACH settlement is driven by NACHA return files received 1-3
business days after transfer initiation. Here we poll every 2 minutes and
settle all pending ACH payments, which lets the dev/test cycle work without
waiting for real bank settlement windows.

Wired into Celery Beat in celery_app.py.
"""

import asyncio
import uuid

from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.payments import repository as payments_repository
from app.payments import service as payments_service
from shared.logger import get_logger
from shared.settings import (
    CASH_ACCOUNT_ID,
    DATABASE_URL,
    LIABILITY_ACCOUNT_ID,
)
from workers.celery_app import celery_app

logger = get_logger(__name__)


@celery_app.task(name="workers.jobs.payments.ach_settlement.run_ach_settlement")
def run_ach_settlement() -> None:
    asyncio.run(_run())


async def _run() -> None:
    engine = create_async_engine(DATABASE_URL)
    async_session = async_sessionmaker(engine, expire_on_commit=False)

    try:
        async with async_session() as session:
            pending = await payments_repository.get_pending_ach(session)

        if not pending:
            logger.debug("ach_settlement: no pending ACH payments")
            return

        logger.info("ach_settlement: settling %d pending ACH payments", len(pending))

        liability_account_id = uuid.UUID(LIABILITY_ACCOUNT_ID)
        cash_account_id = uuid.UUID(CASH_ACCOUNT_ID)

        for payment in pending:
            async with async_session() as session:
                try:
                    await payments_service.handle_payment_succeeded(
                        session=session,
                        processor_payment_id=payment.processor_payment_id,
                        liability_account_id=liability_account_id,
                        cash_account_id=cash_account_id,
                    )
                    logger.info(
                        "ach_settlement: settled | payment_id=%s processor_payment_id=%s amount=%d",
                        payment.id,
                        payment.processor_payment_id,
                        payment.amount,
                    )
                except Exception:
                    logger.exception(
                        "ach_settlement: failed to settle | payment_id=%s processor_payment_id=%s",
                        payment.id,
                        payment.processor_payment_id,
                    )
    finally:
        await engine.dispose()
