import asyncio
from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.bills import repository as bills_repository
from shared.logger import get_logger
from shared.settings import DATABASE_URL
from workers.celery_app import celery_app
from workers.jobs.bills import executor

logger = get_logger(__name__)


@celery_app.task(name="workers.jobs.bills.scheduler.run_bill_scheduler")
def run_bill_scheduler() -> None:
    asyncio.run(_run())


async def _run() -> None:
    now = datetime.now(timezone.utc)
    logger.info("bill scheduler started | now=%s", now)

    engine = create_async_engine(DATABASE_URL)
    async_session = async_sessionmaker(engine, expire_on_commit=False)

    try:
        async with async_session() as session:
            due_bills = await bills_repository.get_due_bills(session, now=now)
            if not due_bills:
                logger.info("bill scheduler: no due bills found")
                return

            logger.info("bill scheduler: found %d due bills", len(due_bills))
            for bill in due_bills:
                try:
                    await executor.execute_bill(session=session, bill_id=bill.id)
                except Exception:
                    logger.exception(
                        "bill scheduler: execution failed | bill_id=%s", bill.id
                    )
    finally:
        await engine.dispose()
