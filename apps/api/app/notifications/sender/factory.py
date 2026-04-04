from app.notifications.sender.base import NotificationSender
from shared.enums.notification_sender import SupportedNotificationSender
from shared.settings import NOTIFICATION_SENDER


def get_sender() -> NotificationSender:
    """Return the configured NotificationSender. Defaults to StubSender."""
    if NOTIFICATION_SENDER == SupportedNotificationSender.SMTP:
        from app.notifications.sender.adapters.smtp import SmtpSender
        from shared.settings import (
            SMTP_FROM,
            SMTP_HOST,
            SMTP_PASSWORD,
            SMTP_PORT,
            SMTP_USER,
        )

        return SmtpSender(
            host=SMTP_HOST,
            port=SMTP_PORT,
            user=SMTP_USER,
            password=SMTP_PASSWORD,
            from_addr=SMTP_FROM,
        )

    if NOTIFICATION_SENDER == SupportedNotificationSender.TWILIO:
        from app.notifications.sender.adapters.twilio import TwilioSender
        from shared.settings import (
            TWILIO_ACCOUNT_SID,
            TWILIO_AUTH_TOKEN,
            TWILIO_FROM_NUMBER,
        )

        return TwilioSender(
            account_sid=TWILIO_ACCOUNT_SID,
            auth_token=TWILIO_AUTH_TOKEN,
            from_number=TWILIO_FROM_NUMBER,
        )

    from app.notifications.sender.adapters.stub import StubSender

    return StubSender()
