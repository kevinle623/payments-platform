from enum import StrEnum


class SupportedProcessorType(StrEnum):
    STRIPE = "stripe"
    ACH = "ach"
