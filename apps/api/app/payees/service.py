import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.payees import repository
from app.payees.schemas import PayeeDTO
from shared.exceptions import PaymentNotFoundError
from shared.logger import get_logger

logger = get_logger(__name__)


async def create_payee(
    session: AsyncSession,
    name: str,
    payee_type: str,
    account_number: str,
    routing_number: str,
    currency: str,
) -> PayeeDTO:
    try:
        payee = await repository.create(
            session=session,
            name=name,
            payee_type=payee_type,
            account_number=account_number,
            routing_number=routing_number,
            currency=currency,
        )
        await session.commit()
        logger.info("payee created | payee_id=%s name=%s", payee.id, payee.name)
        return payee
    except Exception:
        await session.rollback()
        raise


async def get_payee(
    session: AsyncSession,
    payee_id: uuid.UUID,
) -> PayeeDTO:
    payee = await repository.get_by_id(session, payee_id)
    if payee is None:
        raise PaymentNotFoundError(f"Payee not found: {payee_id}")
    return payee


async def list_payees(
    session: AsyncSession,
    limit: int = 100,
    offset: int = 0,
) -> list[PayeeDTO]:
    return await repository.list_payees(session, limit=limit, offset=offset)
