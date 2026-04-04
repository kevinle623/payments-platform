from typing import Protocol


class NotificationSender(Protocol):
    """
    Deliver a notification to a recipient.

    Concrete implementations live in sender/adapters/:
      StubSender  -- logs only, used in development and tests
      SmtpSender  -- email via SMTP
      TwilioSender -- SMS via Twilio (stub, ready to wire up)
    """

    async def send(self, to: str, subject: str, body: str) -> None:
        """
        Send a notification.

        Args:
            to:      Recipient address -- email address or phone number
                     depending on the channel.
            subject: Short summary line (used as email subject or SMS prefix).
            body:    Full message body.
        """
        ...
