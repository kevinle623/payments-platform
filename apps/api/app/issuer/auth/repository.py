import uuid
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.issuer.auth.models import IssuerAuthDecision, IssuerAuthorization
from app.issuer.auth.schemas import IssuerAuthorizationDTO


async def _get_orm_by_idempotency_key(
    session: AsyncSession,
    idempotency_key: str,
) -> IssuerAuthorization | None:
    result = await session.execute(
        select(IssuerAuthorization).where(
            IssuerAuthorization.idempotency_key == idempotency_key
        )
    )
    return result.scalar_one_or_none()


async def get_by_idempotency_key(
    session: AsyncSession,
    idempotency_key: str,
) -> IssuerAuthorizationDTO | None:
    orm_object = await _get_orm_by_idempotency_key(session, idempotency_key)
    if orm_object is None:
        return None
    return IssuerAuthorizationDTO.model_validate(orm_object)


async def get_stale_approved(
    session: AsyncSession,
    older_than: datetime,
) -> list[IssuerAuthorizationDTO]:
    result = await session.execute(
        select(IssuerAuthorization)
        .where(IssuerAuthorization.decision == IssuerAuthDecision.APPROVED)
        .where(IssuerAuthorization.card_id.isnot(None))
        .where(IssuerAuthorization.created_at < older_than)
    )
    return [
        IssuerAuthorizationDTO.model_validate(row) for row in result.scalars().all()
    ]


async def mark_expired(
    session: AsyncSession,
    authorization_id: uuid.UUID,
) -> None:
    result = await session.execute(
        select(IssuerAuthorization).where(IssuerAuthorization.id == authorization_id)
    )
    auth = result.scalar_one()
    auth.decision = IssuerAuthDecision.EXPIRED
    await session.flush()


async def create(
    session: AsyncSession,
    idempotency_key: str,
    decision: IssuerAuthDecision,
    decline_reason: str | None,
    amount: int,
    currency: str,
    card_id: uuid.UUID | None = None,
) -> IssuerAuthorizationDTO:
    record = IssuerAuthorization(
        idempotency_key=idempotency_key,
        card_id=card_id,
        decision=decision,
        decline_reason=decline_reason,
        amount=amount,
        currency=currency,
    )
    session.add(record)
    await session.flush()
    return IssuerAuthorizationDTO.model_validate(record)
