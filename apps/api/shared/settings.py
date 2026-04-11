from os import environ

from dotenv import load_dotenv

from shared.enums.notification_sender import SupportedNotificationSender
from shared.enums.processor import SupportedProcessorType

load_dotenv()

# Stripe keys are only required when PROCESSOR=stripe
STRIPE_SECRET_KEY = environ.get("STRIPE_SECRET_KEY", "")
STRIPE_WEBHOOK_SECRET = environ.get("STRIPE_WEBHOOK_SECRET", "")

DATABASE_URL = environ.get(
    "DATABASE_URL", "postgresql+asyncpg://postgres:postgres@localhost:5432/payments"
)
REDIS_URL = environ.get("REDIS_URL", "redis://localhost:6379/0")
RABBITMQ_URL = environ.get("RABBITMQ_URL", "amqp://guest:guest@localhost:5672/")
PROCESSOR = SupportedProcessorType(
    environ.get("PROCESSOR", SupportedProcessorType.STRIPE)
)
# Bill payments use a separate processor -- defaults to ACH (bank-to-bank direct debit)
BILL_PROCESSOR = SupportedProcessorType(
    environ.get("BILL_PROCESSOR", SupportedProcessorType.ACH)
)

EXPENSE_ACCOUNT_ID = environ.get(
    "EXPENSE_ACCOUNT_ID", "00000000-0000-0000-0000-000000000001"
)
LIABILITY_ACCOUNT_ID = environ.get(
    "LIABILITY_ACCOUNT_ID", "00000000-0000-0000-0000-000000000002"
)
CASH_ACCOUNT_ID = environ.get("CASH_ACCOUNT_ID", "00000000-0000-0000-0000-000000000003")

# Notification sender -- defaults to stub (log only), set to smtp or twilio for real delivery
NOTIFICATION_SENDER = SupportedNotificationSender(
    environ.get("NOTIFICATION_SENDER", SupportedNotificationSender.STUB)
)

# SMTP settings -- used when NOTIFICATION_SENDER=smtp
SMTP_HOST = environ.get("SMTP_HOST", "")
SMTP_PORT = int(environ.get("SMTP_PORT", "587"))
SMTP_USER = environ.get("SMTP_USER", "")
SMTP_PASSWORD = environ.get("SMTP_PASSWORD", "")
SMTP_FROM = environ.get("SMTP_FROM", "noreply@payments-platform.local")

# Twilio settings -- used when NOTIFICATION_SENDER=twilio
TWILIO_ACCOUNT_SID = environ.get("TWILIO_ACCOUNT_SID", "")
TWILIO_AUTH_TOKEN = environ.get("TWILIO_AUTH_TOKEN", "")
TWILIO_FROM_NUMBER = environ.get("TWILIO_FROM_NUMBER", "")
