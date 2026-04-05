from app.issuer.auth import service as auth_service
from app.issuer.cards import service as cards_service
from shared.enums.currency import Currency


async def test_list_cardholders_returns_created_rows(session):
    first = await cards_service.create_cardholder(
        session,
        name="User One",
        email="user1@example.com",
    )
    second = await cards_service.create_cardholder(
        session,
        name="User Two",
        email="user2@example.com",
    )

    cardholders = await cards_service.list_cardholders(session=session)
    ids = {cardholder.id for cardholder in cardholders}
    assert first.id in ids
    assert second.id in ids


async def test_list_cards_returns_created_rows(session):
    cardholder = await cards_service.create_cardholder(
        session,
        name="Card Holder",
        email="holder@example.com",
    )
    first = await cards_service.create_card(
        session,
        cardholder_id=cardholder.id,
        credit_limit=20000,
        currency=Currency.USD,
    )
    second = await cards_service.create_card(
        session,
        cardholder_id=cardholder.id,
        credit_limit=30000,
        currency=Currency.USD,
    )

    cards = await cards_service.list_cards(session=session)
    ids = {card.id for card in cards}
    assert first.id in ids
    assert second.id in ids


async def test_list_card_authorizations_returns_card_history(session):
    cardholder = await cards_service.create_cardholder(
        session,
        name="Auth User",
        email="auth-user@example.com",
    )
    card = await cards_service.create_card(
        session,
        cardholder_id=cardholder.id,
        credit_limit=10000,
        currency=Currency.USD,
    )

    await auth_service.evaluate(
        session=session,
        idempotency_key="idem-auth-history-001",
        amount=1000,
        currency="usd",
        metadata={},
        card_id=card.id,
    )
    await auth_service.evaluate(
        session=session,
        idempotency_key="idem-auth-history-002",
        amount=1200,
        currency="usd",
        metadata={},
        card_id=card.id,
    )

    auths = await cards_service.list_card_authorizations(session=session, card_id=card.id)
    keys = {auth.idempotency_key for auth in auths}
    assert "idem-auth-history-001" in keys
    assert "idem-auth-history-002" in keys
