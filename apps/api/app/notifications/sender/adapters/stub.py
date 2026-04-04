from shared.logger import get_logger

logger = get_logger(__name__)


class StubSender:
    """
    Logs the notification without delivering it.
    Default when NOTIFICATION_SENDER is not set or set to 'stub'.
    Safe to use in tests and local development.
    """

    async def send(self, to: str, subject: str, body: str) -> None:
        logger.info(
            "stub notification | to=%s subject=%r body=%r",
            to,
            subject,
            body,
        )
