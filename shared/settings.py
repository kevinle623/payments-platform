from os import environ

from dotenv import load_dotenv

from shared.processors.base import SupportedProcessorType

load_dotenv()

STRIPE_SECRET_KEY = environ["STRIPE_SECRET_KEY"]
STRIPE_WEBHOOK_SECRET = environ["STRIPE_WEBHOOK_SECRET"]

DATABASE_URL = environ.get(
    "DATABASE_URL", "postgresql+asyncpg://postgres:postgres@localhost:5432/payments"
)
REDIS_URL = environ.get("REDIS_URL", "redis://localhost:6379/0")
RABBITMQ_URL = environ.get("RABBITMQ_URL", "amqp://guest:guest@localhost:5672/")
PROCESSOR = SupportedProcessorType(
    environ.get("PROCESSOR", SupportedProcessorType.STRIPE)
)
