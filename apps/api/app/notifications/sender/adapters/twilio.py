"""
Twilio SMS adapter -- stub, ready to wire up.

To activate:
  1. pip install twilio
  2. Set NOTIFICATION_SENDER=twilio in your environment
  3. Set TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, TWILIO_FROM_NUMBER
  4. Replace the stub body below with:
       from twilio.rest import Client
       client = Client(self.account_sid, self.auth_token)
       client.messages.create(body=f"{subject}: {body}", from_=self.from_number, to=to)
"""

from shared.logger import get_logger

logger = get_logger(__name__)


class TwilioSender:
    """
    Sends SMS notifications via Twilio.
    Currently a stub -- logs instead of calling the Twilio API.
    """

    def __init__(
        self,
        account_sid: str,
        auth_token: str,
        from_number: str,
    ) -> None:
        self.account_sid = account_sid
        self.auth_token = auth_token
        self.from_number = from_number

    async def send(self, to: str, subject: str, body: str) -> None:
        # stub -- replace with real Twilio client call when ready
        logger.info(
            "twilio sms stub | to=%s subject=%r body=%r",
            to,
            subject,
            body,
        )
