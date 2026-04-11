import asyncio
import json
from collections.abc import Awaitable, Callable

import aio_pika

from shared.logger import get_logger
from shared.settings import RABBITMQ_URL

logger = get_logger(__name__)


async def run_consumer(
    exchange_name: str,
    queue_name: str,
    routing_keys: list[str],
    handler: Callable[[str, dict], Awaitable[None]],
) -> None:
    """Connect to RabbitMQ, declare queue bound to routing_keys, consume forever.

    Failed messages are nacked (no requeue) and routed to a per-queue dead
    letter queue via the exchange's DLX. Each consumer gets its own DLQ named
    {queue_name}.dlq so poison messages are isolated and inspectable.
    """
    connection = await aio_pika.connect_robust(RABBITMQ_URL)
    async with connection:
        channel = await connection.channel()
        await channel.set_qos(prefetch_count=1)

        exchange = await channel.declare_exchange(
            exchange_name,
            aio_pika.ExchangeType.TOPIC,
            durable=True,
        )

        # Dead letter exchange -- one per main exchange, topic so routing key is preserved
        dlx_name = f"{exchange_name}.dlx"
        dlx = await channel.declare_exchange(
            dlx_name,
            aio_pika.ExchangeType.TOPIC,
            durable=True,
        )

        # Per-queue DLQ bound to DLX using queue name as routing key
        dlq_name = f"{queue_name}.dlq"
        dlq = await channel.declare_queue(dlq_name, durable=True)
        await dlq.bind(dlx, routing_key=queue_name)

        # Main queue routes dead letters to DLX with queue name as routing key
        queue = await channel.declare_queue(
            queue_name,
            durable=True,
            arguments={
                "x-dead-letter-exchange": dlx_name,
                "x-dead-letter-routing-key": queue_name,
            },
        )
        for routing_key in routing_keys:
            await queue.bind(exchange, routing_key=routing_key)

        logger.info(
            "consumer ready | exchange=%s queue=%s dlq=%s routing_keys=%s",
            exchange_name,
            queue_name,
            dlq_name,
            routing_keys,
        )

        async with queue.iterator() as messages:
            async for message in messages:
                async with message.process(requeue=False):
                    try:
                        payload = json.loads(message.body)
                        event_type = message.type or message.routing_key
                        await handler(event_type, payload)
                    except Exception:
                        logger.exception(
                            "consumer handler failed, routing to DLQ | queue=%s dlq=%s message_id=%s",
                            queue_name,
                            dlq_name,
                            message.message_id,
                        )
                        raise


def start(
    exchange_name: str,
    queue_name: str,
    routing_keys: list[str],
    handler: Callable[[str, dict], Awaitable[None]],
) -> None:
    """Entrypoint for running a consumer as a standalone process."""
    asyncio.run(run_consumer(exchange_name, queue_name, routing_keys, handler))
