import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.issuer.controls import repository
from app.issuer.controls.schemas import MCCBlockDTO, VelocityRuleDTO
from shared.logger import get_logger

logger = get_logger(__name__)


async def check_controls(
    session: AsyncSession,
    card_id: uuid.UUID,
    available_credit: int,
    amount: int,
    metadata: dict,
) -> str | None:
    """
    Run all spend controls for the card. Returns a decline reason string if
    any control fails, or None if all pass.
    """
    # 1. balance check
    if available_credit < amount:
        logger.info(
            "control check: insufficient funds | card_id=%s available=%d requested=%d",
            card_id,
            available_credit,
            amount,
        )
        return "insufficient_funds"

    # 2. MCC block
    mcc = metadata.get("mcc")
    if mcc:
        block = await repository.get_mcc_block(session, card_id, mcc)
        if block:
            logger.info(
                "control check: mcc blocked | card_id=%s mcc=%s",
                card_id,
                mcc,
            )
            return "mcc_blocked"

    # 3. velocity limits
    rules = await repository.get_velocity_rules_for_card(session, card_id)
    for rule in rules:
        recent_spend = await _get_recent_approved_spend(
            session, card_id, rule.window_seconds
        )
        if recent_spend + amount > rule.max_amount:
            logger.info(
                "control check: velocity exceeded | card_id=%s recent=%d amount=%d max=%d window=%ds",
                card_id,
                recent_spend,
                amount,
                rule.max_amount,
                rule.window_seconds,
            )
            return "velocity_exceeded"

    return None


async def _get_recent_approved_spend(
    session: AsyncSession,
    card_id: uuid.UUID,
    window_seconds: int,
) -> int:
    from datetime import datetime, timedelta, timezone

    from sqlalchemy import func, select

    from app.issuer.auth.models import IssuerAuthDecision, IssuerAuthorization

    since = datetime.now(timezone.utc) - timedelta(seconds=window_seconds)
    result = await session.execute(
        select(func.coalesce(func.sum(IssuerAuthorization.amount), 0)).where(
            IssuerAuthorization.card_id == card_id,
            IssuerAuthorization.decision == IssuerAuthDecision.APPROVED,
            IssuerAuthorization.created_at >= since,
        )
    )
    return result.scalar_one()


async def add_mcc_block(
    session: AsyncSession,
    card_id: uuid.UUID,
    mcc: str,
) -> MCCBlockDTO:
    block = await repository.create_mcc_block(session, card_id=card_id, mcc=mcc)
    logger.info("mcc block added | card_id=%s mcc=%s", card_id, mcc)
    return block


async def remove_mcc_block(
    session: AsyncSession,
    card_id: uuid.UUID,
    mcc: str,
) -> bool:
    removed = await repository.delete_mcc_block(session, card_id=card_id, mcc=mcc)
    if removed:
        logger.info("mcc block removed | card_id=%s mcc=%s", card_id, mcc)
    return removed


async def add_velocity_rule(
    session: AsyncSession,
    card_id: uuid.UUID,
    max_amount: int,
    window_seconds: int,
) -> VelocityRuleDTO:
    rule = await repository.create_velocity_rule(
        session, card_id=card_id, max_amount=max_amount, window_seconds=window_seconds
    )
    logger.info(
        "velocity rule added | card_id=%s max_amount=%d window=%ds",
        card_id,
        max_amount,
        window_seconds,
    )
    return rule


async def remove_velocity_rule(
    session: AsyncSession,
    card_id: uuid.UUID,
    rule_id: uuid.UUID,
) -> bool:
    removed = await repository.delete_velocity_rule(
        session, rule_id=rule_id, card_id=card_id
    )
    if removed:
        logger.info("velocity rule removed | card_id=%s rule_id=%s", card_id, rule_id)
    return removed
