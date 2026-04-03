from sqlalchemy.ext.asyncio import AsyncSession

from app.issuer.auth import repository
from app.issuer.auth.models import IssuerAuthDecision
from app.issuer.auth.schemas import IssuerAuthorizationDTO
from shared.logger import get_logger

logger = get_logger(__name__)


async def evaluate(
    session: AsyncSession,
    idempotency_key: str,
    amount: int,
    currency: str,
    metadata: dict,
) -> IssuerAuthorizationDTO:
    # idempotency -- if we already evaluated this request, return the existing decision
    existing = await repository.get_by_idempotency_key(session, idempotency_key)
    if existing:
        logger.info(
            "issuer auth idempotency hit | idempotency_key=%s decision=%s",
            idempotency_key,
            existing.decision,
        )
        return existing

    # stub: always approve -- controls and balance checks plug in here later
    decision = IssuerAuthDecision.APPROVED
    decline_reason = None

    record = await repository.create(
        session,
        idempotency_key=idempotency_key,
        decision=decision,
        decline_reason=decline_reason,
        amount=amount,
        currency=currency,
    )

    logger.info(
        "issuer auth decision | idempotency_key=%s decision=%s amount=%d currency=%s",
        idempotency_key,
        decision,
        amount,
        currency,
    )

    return record
