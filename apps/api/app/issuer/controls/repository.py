import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.issuer.controls.models import MCCBlock, VelocityRule
from app.issuer.controls.schemas import MCCBlockDTO, VelocityRuleDTO


# -- MCC blocks --


async def get_mcc_block(
    session: AsyncSession,
    card_id: uuid.UUID,
    mcc: str,
) -> MCCBlockDTO | None:
    result = await session.execute(
        select(MCCBlock).where(MCCBlock.card_id == card_id, MCCBlock.mcc == mcc)
    )
    orm_object = result.scalar_one_or_none()
    if orm_object is None:
        return None
    return MCCBlockDTO.model_validate(orm_object)


async def get_mcc_blocks_for_card(
    session: AsyncSession,
    card_id: uuid.UUID,
) -> list[MCCBlockDTO]:
    result = await session.execute(
        select(MCCBlock).where(MCCBlock.card_id == card_id)
    )
    return [MCCBlockDTO.model_validate(row) for row in result.scalars().all()]


async def create_mcc_block(
    session: AsyncSession,
    card_id: uuid.UUID,
    mcc: str,
) -> MCCBlockDTO:
    block = MCCBlock(card_id=card_id, mcc=mcc)
    session.add(block)
    await session.flush()
    return MCCBlockDTO.model_validate(block)


async def delete_mcc_block(
    session: AsyncSession,
    card_id: uuid.UUID,
    mcc: str,
) -> bool:
    result = await session.execute(
        select(MCCBlock).where(MCCBlock.card_id == card_id, MCCBlock.mcc == mcc)
    )
    orm_object = result.scalar_one_or_none()
    if orm_object is None:
        return False
    await session.delete(orm_object)
    await session.flush()
    return True


# -- velocity rules --


async def get_velocity_rules_for_card(
    session: AsyncSession,
    card_id: uuid.UUID,
) -> list[VelocityRuleDTO]:
    result = await session.execute(
        select(VelocityRule).where(VelocityRule.card_id == card_id)
    )
    return [VelocityRuleDTO.model_validate(row) for row in result.scalars().all()]


async def create_velocity_rule(
    session: AsyncSession,
    card_id: uuid.UUID,
    max_amount: int,
    window_seconds: int,
) -> VelocityRuleDTO:
    rule = VelocityRule(
        card_id=card_id,
        max_amount=max_amount,
        window_seconds=window_seconds,
    )
    session.add(rule)
    await session.flush()
    return VelocityRuleDTO.model_validate(rule)


async def delete_velocity_rule(
    session: AsyncSession,
    rule_id: uuid.UUID,
    card_id: uuid.UUID,
) -> bool:
    result = await session.execute(
        select(VelocityRule).where(
            VelocityRule.id == rule_id,
            VelocityRule.card_id == card_id,
        )
    )
    orm_object = result.scalar_one_or_none()
    if orm_object is None:
        return False
    await session.delete(orm_object)
    await session.flush()
    return True
