import asyncio
import smtplib
from email.mime.text import MIMEText

from shared.logger import get_logger

logger = get_logger(__name__)


class SmtpSender:
    """
    Delivers email via SMTP.
    Uses asyncio.to_thread so the consumer event loop is not blocked by the
    synchronous smtplib call.

    Required settings: SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASSWORD, SMTP_FROM
    """

    def __init__(
        self,
        host: str,
        port: int,
        user: str,
        password: str,
        from_addr: str,
    ) -> None:
        self.host = host
        self.port = port
        self.user = user
        self.password = password
        self.from_addr = from_addr

    async def send(self, to: str, subject: str, body: str) -> None:
        await asyncio.to_thread(self._send_sync, to, subject, body)

    def _send_sync(self, to: str, subject: str, body: str) -> None:
        msg = MIMEText(body)
        msg["Subject"] = subject
        msg["From"] = self.from_addr
        msg["To"] = to
        with smtplib.SMTP(self.host, self.port) as smtp:
            smtp.starttls()
            smtp.login(self.user, self.password)
            smtp.send_message(msg)
        logger.info("smtp email sent | to=%s subject=%r", to, subject)
