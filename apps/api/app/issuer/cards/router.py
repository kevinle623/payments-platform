import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.issuer.auth.schemas import IssuerAuthorizationDTO
from app.issuer.cards import service
from app.issuer.cards.schemas import (
    CardBalanceResponse,
    CardDTO,
    CardholderDTO,
    CreateCardholderRequest,
    CreateCardRequest,
)
from app.issuer.controls import service as controls_service
from app.issuer.controls.schemas import (
    CreateMCCBlockRequest,
    CreateVelocityRuleRequest,
    MCCBlockDTO,
    VelocityRuleDTO,
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


@router.get("/cardholders", response_model=list[CardholderDTO])
async def list_cardholders(
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    session: AsyncSession = Depends(get_db),
):
    return await service.list_cardholders(session=session, limit=limit, offset=offset)


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


@router.get("/cards", response_model=list[CardDTO])
async def list_cards(
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    session: AsyncSession = Depends(get_db),
):
    return await service.list_cards(session=session, limit=limit, offset=offset)


@router.get("/cards/{card_id}/balance", response_model=CardBalanceResponse)
async def get_card_balance(
    card_id: uuid.UUID,
    session: AsyncSession = Depends(get_db),
):
    return await service.get_card_balance(session, card_id)


@router.get(
    "/cards/{card_id}/authorizations", response_model=list[IssuerAuthorizationDTO]
)
async def list_card_authorizations(
    card_id: uuid.UUID,
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    session: AsyncSession = Depends(get_db),
):
    return await service.list_card_authorizations(
        session=session,
        card_id=card_id,
        limit=limit,
        offset=offset,
    )


# -- spend controls --


@router.get("/cards/{card_id}/controls/mcc-blocks", response_model=list[MCCBlockDTO])
async def list_mcc_blocks(
    card_id: uuid.UUID,
    session: AsyncSession = Depends(get_db),
):
    from app.issuer.controls import repository as controls_repository

    return await controls_repository.get_mcc_blocks_for_card(session, card_id)


@router.post(
    "/cards/{card_id}/controls/mcc-blocks", response_model=MCCBlockDTO, status_code=201
)
async def add_mcc_block(
    card_id: uuid.UUID,
    request: CreateMCCBlockRequest,
    session: AsyncSession = Depends(get_db),
):
    block = await controls_service.add_mcc_block(
        session, card_id=card_id, mcc=request.mcc
    )
    await session.commit()
    return block


@router.delete("/cards/{card_id}/controls/mcc-blocks/{mcc}", status_code=204)
async def remove_mcc_block(
    card_id: uuid.UUID,
    mcc: str,
    session: AsyncSession = Depends(get_db),
):
    await controls_service.remove_mcc_block(session, card_id=card_id, mcc=mcc)
    await session.commit()


@router.get(
    "/cards/{card_id}/controls/velocity-rules", response_model=list[VelocityRuleDTO]
)
async def list_velocity_rules(
    card_id: uuid.UUID,
    session: AsyncSession = Depends(get_db),
):
    from app.issuer.controls import repository as controls_repository

    return await controls_repository.get_velocity_rules_for_card(session, card_id)


@router.post(
    "/cards/{card_id}/controls/velocity-rules",
    response_model=VelocityRuleDTO,
    status_code=201,
)
async def add_velocity_rule(
    card_id: uuid.UUID,
    request: CreateVelocityRuleRequest,
    session: AsyncSession = Depends(get_db),
):
    rule = await controls_service.add_velocity_rule(
        session,
        card_id=card_id,
        max_amount=request.max_amount,
        window_seconds=request.window_seconds,
    )
    await session.commit()
    return rule


@router.delete("/cards/{card_id}/controls/velocity-rules/{rule_id}", status_code=204)
async def remove_velocity_rule(
    card_id: uuid.UUID,
    rule_id: uuid.UUID,
    session: AsyncSession = Depends(get_db),
):
    await controls_service.remove_velocity_rule(
        session, card_id=card_id, rule_id=rule_id
    )
    await session.commit()
