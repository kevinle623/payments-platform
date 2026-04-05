import uuid

from workers.consumers.payments import reporting


def test_resolve_entity_id_prefers_payment_id():
    payment_id = uuid.uuid4()
    resolved = reporting._resolve_entity_id(
        "bill.executed",
        {
            "payment_id": str(payment_id),
            "bill_id": str(uuid.uuid4()),
        },
    )
    assert resolved == payment_id


def test_resolve_entity_id_uses_deterministic_bill_fallback():
    bill_id = uuid.uuid4()
    first = reporting._resolve_entity_id(
        "bill.failed",
        {"bill_id": str(bill_id)},
    )
    second = reporting._resolve_entity_id(
        "bill.failed",
        {"bill_id": str(bill_id)},
    )
    assert first is not None
    assert first == second


def test_resolve_entity_id_returns_none_when_missing_keys():
    resolved = reporting._resolve_entity_id("bill.failed", {})
    assert resolved is None
