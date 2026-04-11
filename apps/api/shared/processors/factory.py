from shared.enums.processor import SupportedProcessorType
from shared.processors.base import PaymentProcessor
from shared.settings import BILL_PROCESSOR, PROCESSOR


def get_processor() -> PaymentProcessor:
    """Returns the card/checkout processor (driven by PROCESSOR env var)."""
    return _build(PROCESSOR)


def get_bill_processor() -> PaymentProcessor:
    """Returns the bill payment processor (driven by BILL_PROCESSOR env var, defaults to ACH)."""
    return _build(BILL_PROCESSOR)


def _build(processor_type: SupportedProcessorType) -> PaymentProcessor:
    if processor_type == SupportedProcessorType.STRIPE:
        from shared.processors.adapters.stripe import StripeAdapter

        return StripeAdapter()
    if processor_type == SupportedProcessorType.ACH:
        from shared.processors.adapters.ach import ACHAdapter

        return ACHAdapter()
    raise ValueError(f"Unknown processor: {processor_type}")
