from enum import StrEnum


class SupportedNotificationSender(StrEnum):
    STUB = "stub"
    SMTP = "smtp"
    TWILIO = "twilio"
