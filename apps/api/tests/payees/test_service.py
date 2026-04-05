import uuid

import pytest

from app.payees import service
from app.payees.models import PayeeType
from shared.enums.currency import Currency
from shared.exceptions import PaymentNotFoundError


async def test_create_payee(session):
    payee = await service.create_payee(
        session=session,
        name="Hydro One",
        payee_type=PayeeType.UTILITY,
        account_number="1234567890",
        routing_number="021000021",
        currency=Currency.USD,
    )

    assert payee.id is not None
    assert payee.name == "Hydro One"
    assert payee.payee_type == PayeeType.UTILITY
    assert payee.account_number == "1234567890"
    assert payee.routing_number == "021000021"
    assert payee.currency == Currency.USD


async def test_list_payees(session):
    payee_a = await service.create_payee(
        session=session,
        name="Enbridge",
        payee_type=PayeeType.UTILITY,
        account_number="1111111111",
        routing_number="021000021",
        currency=Currency.USD,
    )
    payee_b = await service.create_payee(
        session=session,
        name="Mortgage Lender",
        payee_type=PayeeType.MORTGAGE,
        account_number="2222222222",
        routing_number="021000021",
        currency=Currency.USD,
    )

    payees = await service.list_payees(session=session)
    payee_ids = {payee.id for payee in payees}
    assert payee_a.id in payee_ids
    assert payee_b.id in payee_ids


async def test_get_payee(session):
    payee = await service.create_payee(
        session=session,
        name="Card Issuer",
        payee_type=PayeeType.CREDIT_CARD,
        account_number="3333333333",
        routing_number="021000021",
        currency=Currency.USD,
    )

    fetched = await service.get_payee(session=session, payee_id=payee.id)
    assert fetched.id == payee.id
    assert fetched.name == "Card Issuer"


async def test_get_payee_not_found_raises(session):
    with pytest.raises(PaymentNotFoundError):
        await service.get_payee(session=session, payee_id=uuid.uuid4())
