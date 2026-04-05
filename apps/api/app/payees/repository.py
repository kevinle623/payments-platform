import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.payees.models import Payee
from app.payees.schemas import PayeeDTO


async def _get_payee_orm(session: AsyncSession, payee_id: uuid.UUID) -> Payee | None:
    result = await session.execute(select(Payee).where(Payee.id == payee_id))
    return result.scalar_one_or_none()


async def create(
    session: AsyncSession,
    name: str,
    payee_type: str,
    account_number: str,
    routing_number: str,
    currency: str,
) -> PayeeDTO:
    payee = Payee(
        name=name,
        payee_type=payee_type,
        account_number=account_number,
        routing_number=routing_number,
        currency=currency,
    )
    session.add(payee)
    await session.flush()
    return PayeeDTO.model_validate(payee)


async def get_by_id(
    session: AsyncSession,
    payee_id: uuid.UUID,
) -> PayeeDTO | None:
    orm_object = await _get_payee_orm(session, payee_id)
    if orm_object is None:
        return None
    return PayeeDTO.model_validate(orm_object)


async def list_payees(
    session: AsyncSession,
    limit: int = 100,
    offset: int = 0,
) -> list[PayeeDTO]:
    result = await session.execute(
        select(Payee).order_by(Payee.created_at.desc()).limit(limit).offset(offset)
    )
    return [PayeeDTO.model_validate(row) for row in result.scalars().all()]
