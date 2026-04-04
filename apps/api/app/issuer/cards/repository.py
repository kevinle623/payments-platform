import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.issuer.cards.models import Card, Cardholder, CardholderStatus, CardStatus
from app.issuer.cards.schemas import CardDTO, CardholderDTO

# -- cardholder --


async def _get_cardholder_orm(
    session: AsyncSession, cardholder_id: uuid.UUID
) -> Cardholder | None:
    result = await session.execute(
        select(Cardholder).where(Cardholder.id == cardholder_id)
    )
    return result.scalar_one_or_none()


async def get_cardholder(
    session: AsyncSession, cardholder_id: uuid.UUID
) -> CardholderDTO | None:
    orm_object = await _get_cardholder_orm(session, cardholder_id)
    if orm_object is None:
        return None
    return CardholderDTO.model_validate(orm_object)


async def get_cardholder_by_email(
    session: AsyncSession, email: str
) -> CardholderDTO | None:
    result = await session.execute(select(Cardholder).where(Cardholder.email == email))
    orm_object = result.scalar_one_or_none()
    if orm_object is None:
        return None
    return CardholderDTO.model_validate(orm_object)


async def create_cardholder(
    session: AsyncSession,
    name: str,
    email: str,
) -> CardholderDTO:
    cardholder = Cardholder(
        name=name,
        email=email,
        status=CardholderStatus.ACTIVE,
    )
    session.add(cardholder)
    await session.flush()
    return CardholderDTO.model_validate(cardholder)


# -- card --


async def _get_card_orm(session: AsyncSession, card_id: uuid.UUID) -> Card | None:
    result = await session.execute(select(Card).where(Card.id == card_id))
    return result.scalar_one_or_none()


async def get_card(session: AsyncSession, card_id: uuid.UUID) -> CardDTO | None:
    orm_object = await _get_card_orm(session, card_id)
    if orm_object is None:
        return None
    return CardDTO.model_validate(orm_object)


async def get_cards_by_cardholder(
    session: AsyncSession, cardholder_id: uuid.UUID
) -> list[CardDTO]:
    result = await session.execute(
        select(Card).where(Card.cardholder_id == cardholder_id)
    )
    return [CardDTO.model_validate(row) for row in result.scalars().all()]


async def get_active_card_by_cardholder(
    session: AsyncSession, cardholder_id: uuid.UUID
) -> CardDTO | None:
    result = await session.execute(
        select(Card).where(
            Card.cardholder_id == cardholder_id,
            Card.status == CardStatus.ACTIVE,
        )
    )
    orm_object = result.scalar_one_or_none()
    if orm_object is None:
        return None
    return CardDTO.model_validate(orm_object)


async def create_card(
    session: AsyncSession,
    cardholder_id: uuid.UUID,
    credit_limit: int,
    currency: str,
    available_balance_account_id: uuid.UUID,
    pending_hold_account_id: uuid.UUID,
    last_four: str | None,
) -> CardDTO:
    card = Card(
        cardholder_id=cardholder_id,
        credit_limit=credit_limit,
        currency=currency,
        available_balance_account_id=available_balance_account_id,
        pending_hold_account_id=pending_hold_account_id,
        status=CardStatus.ACTIVE,
        last_four=last_four,
    )
    session.add(card)
    await session.flush()
    return CardDTO.model_validate(card)
