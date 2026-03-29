from os import environ

from dotenv import load_dotenv

from shared.enums.processor import SupportedProcessorType

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

EXPENSE_ACCOUNT_ID = environ.get(
    "EXPENSE_ACCOUNT_ID", "00000000-0000-0000-0000-000000000001"
)
LIABILITY_ACCOUNT_ID = environ.get(
    "LIABILITY_ACCOUNT_ID", "00000000-0000-0000-0000-000000000002"
)
CASH_ACCOUNT_ID = environ.get("CASH_ACCOUNT_ID", "00000000-0000-0000-0000-000000000003")
