"""
Unit tests for the processor factory ACH branch.
"""

from unittest.mock import patch

from shared.enums.processor import SupportedProcessorType
from shared.processors.adapters.ach import ACHAdapter
from shared.processors.adapters.stripe import StripeAdapter
from shared.processors.factory import get_bill_processor, get_processor


def test_get_processor_returns_stripe_adapter():
    with patch("shared.processors.factory.PROCESSOR", SupportedProcessorType.STRIPE):
        processor = get_processor()

    assert isinstance(processor, StripeAdapter)


def test_get_processor_returns_ach_adapter():
    with patch("shared.processors.factory.PROCESSOR", SupportedProcessorType.ACH):
        processor = get_processor()

    assert isinstance(processor, ACHAdapter)


def test_get_bill_processor_returns_ach_by_default():
    with patch("shared.processors.factory.BILL_PROCESSOR", SupportedProcessorType.ACH):
        processor = get_bill_processor()

    assert isinstance(processor, ACHAdapter)


def test_get_bill_processor_can_be_overridden_to_stripe():
    with patch(
        "shared.processors.factory.BILL_PROCESSOR", SupportedProcessorType.STRIPE
    ):
        processor = get_bill_processor()

    assert isinstance(processor, StripeAdapter)
