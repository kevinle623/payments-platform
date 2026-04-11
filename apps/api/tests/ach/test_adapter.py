"""
Unit tests for ACHAdapter -- no DB needed.
"""

import pytest

from shared.exceptions import ProcessorError
from shared.processors.adapters.ach import ACHAdapter
from shared.processors.base import PaymentStatus


async def test_create_payment_intent_returns_pending_with_synthetic_id():
    adapter = ACHAdapter()
    intent = await adapter.create_payment_intent(5000, "usd", {})

    assert intent.status == PaymentStatus.PENDING
    assert intent.processor_id.startswith("ach_")
    assert intent.client_secret == ""
    assert intent.amount == 5000
    assert intent.currency == "usd"


async def test_create_payment_intent_ids_are_unique():
    adapter = ACHAdapter()
    a = await adapter.create_payment_intent(1000, "usd", {})
    b = await adapter.create_payment_intent(1000, "usd", {})

    assert a.processor_id != b.processor_id


async def test_create_payment_intent_preserves_metadata():
    adapter = ACHAdapter()
    meta = {"bill_id": "abc-123", "payee_id": "xyz-456"}
    intent = await adapter.create_payment_intent(3000, "usd", meta)

    assert intent.metadata == meta


async def test_capture_returns_succeeded():
    adapter = ACHAdapter()
    result = await adapter.capture("ach_abc123def")

    assert result.status == PaymentStatus.SUCCEEDED
    assert result.processor_id == "ach_abc123def"


async def test_refund_returns_synthetic_refund_id():
    adapter = ACHAdapter()
    result = await adapter.refund("ach_abc123def", 2500)

    assert result.refund_id.startswith("ach_refund_")
    assert result.processor_id == "ach_abc123def"
    assert result.amount == 2500


async def test_refund_ids_are_unique():
    adapter = ACHAdapter()
    a = await adapter.refund("ach_same", 1000)
    b = await adapter.refund("ach_same", 1000)

    assert a.refund_id != b.refund_id


async def test_parse_webhook_raises_processor_error():
    adapter = ACHAdapter()

    with pytest.raises(ProcessorError):
        await adapter.parse_webhook(b"{}", "sig_abc")
