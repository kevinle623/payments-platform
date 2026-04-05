import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.notifications import repository
from app.notifications.models import NotificationChannel
from app.notifications.schemas import NotificationLogDTO
from app.notifications.sender.base import NotificationSender


async def send_and_log(
    session: AsyncSession,
    sender: NotificationSender,
    event_type: str,
    message: str,
    to_email: str | None = None,
    cardholder_id: uuid.UUID | None = None,
) -> NotificationLogDTO:
    """
    Deliver a notification via sender (if to_email provided) and persist a log row.
    Caller owns the transaction boundary -- no commit here.
    """
    if to_email:
        subject = _subject_for(event_type)
        await sender.send(to_email=to_email, subject=subject, body=message)

    log = await repository.create(
        session=session,
        event_type=event_type,
        channel=NotificationChannel.EMAIL,
        message=message,
        cardholder_id=cardholder_id,
    )
    return log


def _subject_for(event_type: str) -> str:
    subjects = {
        "payment.authorized": "Payment authorized",
        "payment.settled": "Payment completed",
        "payment.refunded": "Refund processed",
        "bill.scheduled": "Bill scheduled",
        "bill.executed": "Bill executed",
        "bill.failed": "Bill failed",
    }
    return subjects.get(event_type, "Payment notification")
