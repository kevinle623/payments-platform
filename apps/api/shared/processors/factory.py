from shared.enums.processor import SupportedProcessorType
from shared.processors.base import PaymentProcessor
from shared.settings import PROCESSOR


def get_processor() -> PaymentProcessor:
    if PROCESSOR == SupportedProcessorType.STRIPE:
        from shared.processors.adapters.stripe import StripeAdapter

        return StripeAdapter()
    raise ValueError(f"Unknown processor: {PROCESSOR}")
