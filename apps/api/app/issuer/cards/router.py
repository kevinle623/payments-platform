import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.issuer.cards import service
from app.issuer.cards.schemas import (
    CardBalanceResponse,
    CardDTO,
    CardholderDTO,
    CreateCardholderRequest,
    CreateCardRequest,
)
from shared.db import get_db

router = APIRouter(prefix="/issuer", tags=["issuer"])


@router.post("/cardholders", response_model=CardholderDTO, status_code=201)
async def create_cardholder(
    request: CreateCardholderRequest,
    session: AsyncSession = Depends(get_db),
):
    cardholder = await service.create_cardholder(
        session,
        name=request.name,
        email=request.email,
    )
    await session.commit()
    return cardholder


@router.get("/cardholders/{cardholder_id}", response_model=CardholderDTO)
async def get_cardholder(
    cardholder_id: uuid.UUID,
    session: AsyncSession = Depends(get_db),
):
    from app.issuer.cards import repository
    cardholder = await repository.get_cardholder(session, cardholder_id)
    if cardholder is None:
        from shared.exceptions import PaymentNotFoundError
        raise PaymentNotFoundError(f"Cardholder not found: {cardholder_id}")
    return cardholder


@router.post("/cards", response_model=CardDTO, status_code=201)
async def create_card(
    request: CreateCardRequest,
    session: AsyncSession = Depends(get_db),
):
    card = await service.create_card(
        session,
        cardholder_id=request.cardholder_id,
        credit_limit=request.credit_limit,
        currency=request.currency,
        last_four=request.last_four,
    )
    await session.commit()
    return card


@router.get("/cards/{card_id}", response_model=CardDTO)
async def get_card(
    card_id: uuid.UUID,
    session: AsyncSession = Depends(get_db),
):
    from app.issuer.cards import repository
    card = await repository.get_card(session, card_id)
    if card is None:
        from shared.exceptions import PaymentNotFoundError
        raise PaymentNotFoundError(f"Card not found: {card_id}")
    return card


@router.get("/cards/{card_id}/balance", response_model=CardBalanceResponse)
async def get_card_balance(
    card_id: uuid.UUID,
    session: AsyncSession = Depends(get_db),
):
    return await service.get_card_balance(session, card_id)
