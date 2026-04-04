import asyncio
import json

import aio_pika
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.outbox import repository
from app.outbox.schemas import OutboxEventDTO
from shared.logger import get_logger
from shared.settings import DATABASE_URL, RABBITMQ_URL
from workers.celery_app import celery_app

logger = get_logger(__name__)

_EXCHANGE_NAME = "payments"


@celery_app.task(name="workers.outbox_poller.poll_and_publish")
def poll_and_publish() -> None:
    asyncio.run(_run())


async def _run() -> None:
    engine = create_async_engine(DATABASE_URL)
    async_session = async_sessionmaker(engine, expire_on_commit=False)

    try:
        async with async_session() as session:
            events = await repository.get_pending(session)

            if not events:
                return

            logger.info("outbox poller: found %d pending events", len(events))

            connection = await aio_pika.connect_robust(RABBITMQ_URL)
            async with connection:
                channel = await connection.channel()
                exchange = await channel.declare_exchange(
                    _EXCHANGE_NAME,
                    aio_pika.ExchangeType.TOPIC,
                    durable=True,
                )
                for event in events:
                    await _publish_event(session, exchange, event)

            await session.commit()
    finally:
        await engine.dispose()


async def _publish_event(
    session: AsyncSession,
    exchange: aio_pika.abc.AbstractExchange,
    event: OutboxEventDTO,
) -> None:
    try:
        await exchange.publish(
            aio_pika.Message(
                body=json.dumps(event.payload).encode(),
                content_type="application/json",
                message_id=str(event.id),
                type=event.event_type,
            ),
            routing_key=event.event_type,
        )
        await repository.mark_published(session, event.id)
        logger.info(
            "outbox event published | event_id=%s event_type=%s",
            event.id,
            event.event_type,
        )
    except Exception:
        await repository.mark_failed(session, event.id)
        logger.exception(
            "outbox event publish failed | event_id=%s event_type=%s",
            event.id,
            event.event_type,
        )
