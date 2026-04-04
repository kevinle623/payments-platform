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
    """Connect to RabbitMQ, declare queue bound to routing_keys, consume forever."""
    connection = await aio_pika.connect_robust(RABBITMQ_URL)
    async with connection:
        channel = await connection.channel()
        await channel.set_qos(prefetch_count=1)

        exchange = await channel.declare_exchange(
            exchange_name,
            aio_pika.ExchangeType.TOPIC,
            durable=True,
        )

        queue = await channel.declare_queue(queue_name, durable=True)
        for routing_key in routing_keys:
            await queue.bind(exchange, routing_key=routing_key)

        logger.info(
            "consumer ready | exchange=%s queue=%s routing_keys=%s",
            exchange_name,
            queue_name,
            routing_keys,
        )

        async with queue.iterator() as messages:
            async for message in messages:
                async with message.process():
                    try:
                        payload = json.loads(message.body)
                        event_type = message.type or message.routing_key
                        await handler(event_type, payload)
                    except Exception:
                        logger.exception(
                            "consumer handler failed | queue=%s message_id=%s",
                            queue_name,
                            message.message_id,
                        )


def start(
    exchange_name: str,
    queue_name: str,
    routing_keys: list[str],
    handler: Callable[[str, dict], Awaitable[None]],
) -> None:
    """Entrypoint for running a consumer as a standalone process."""
    asyncio.run(run_consumer(exchange_name, queue_name, routing_keys, handler))
