import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.bills.models import Bill, BillPayment, BillPaymentStatus, BillStatus
from app.bills.schemas import BillDTO, BillPaymentDTO


async def _get_bill_orm(session: AsyncSession, bill_id: uuid.UUID) -> Bill | None:
    result = await session.execute(select(Bill).where(Bill.id == bill_id))
    return result.scalar_one_or_none()


async def create_bill(
    session: AsyncSession,
    payee_id: uuid.UUID,
    card_id: uuid.UUID | None,
    amount: int,
    currency: str,
    frequency: str,
    next_due_date: datetime,
    status: BillStatus = BillStatus.ACTIVE,
) -> BillDTO:
    bill = Bill(
        payee_id=payee_id,
        card_id=card_id,
        amount=amount,
        currency=currency,
        frequency=frequency,
        next_due_date=next_due_date,
        status=status,
    )
    session.add(bill)
    await session.flush()
    return BillDTO.model_validate(bill)


async def get_bill(
    session: AsyncSession,
    bill_id: uuid.UUID,
) -> BillDTO | None:
    orm_object = await _get_bill_orm(session, bill_id)
    if orm_object is None:
        return None
    return BillDTO.model_validate(orm_object)


async def list_bills(
    session: AsyncSession,
    status: BillStatus | None = None,
    limit: int = 100,
    offset: int = 0,
) -> list[BillDTO]:
    query = select(Bill).order_by(Bill.next_due_date).limit(limit).offset(offset)
    if status is not None:
        query = query.where(Bill.status == status)
    result = await session.execute(query)
    return [BillDTO.model_validate(row) for row in result.scalars().all()]


async def get_due_bills(
    session: AsyncSession,
    now: datetime,
    limit: int = 100,
) -> list[BillDTO]:
    result = await session.execute(
        select(Bill)
        .where(Bill.status == BillStatus.ACTIVE)
        .where(Bill.next_due_date <= now)
        .order_by(Bill.next_due_date)
        .limit(limit)
    )
    return [BillDTO.model_validate(row) for row in result.scalars().all()]


async def update_bill(
    session: AsyncSession,
    bill_id: uuid.UUID,
    updates: dict[str, Any],
) -> BillDTO | None:
    bill = await _get_bill_orm(session, bill_id)
    if bill is None:
        return None

    for field, value in updates.items():
        setattr(bill, field, value)

    await session.flush()
    return BillDTO.model_validate(bill)


async def create_bill_payment(
    session: AsyncSession,
    bill_id: uuid.UUID,
    payment_id: uuid.UUID | None,
    status: BillPaymentStatus,
) -> BillPaymentDTO:
    bill_payment = BillPayment(
        bill_id=bill_id,
        payment_id=payment_id,
        status=status,
    )
    session.add(bill_payment)
    await session.flush()
    return BillPaymentDTO.model_validate(bill_payment)


async def get_bill_payment_by_bill_and_payment(
    session: AsyncSession,
    bill_id: uuid.UUID,
    payment_id: uuid.UUID,
) -> BillPaymentDTO | None:
    result = await session.execute(
        select(BillPayment).where(
            BillPayment.bill_id == bill_id, BillPayment.payment_id == payment_id
        )
    )
    orm_object = result.scalar_one_or_none()
    if orm_object is None:
        return None
    return BillPaymentDTO.model_validate(orm_object)


async def get_latest_bill_payment(
    session: AsyncSession,
    bill_id: uuid.UUID,
) -> BillPaymentDTO | None:
    result = await session.execute(
        select(BillPayment)
        .where(BillPayment.bill_id == bill_id)
        .order_by(BillPayment.executed_at.desc())
        .limit(1)
    )
    orm_object = result.scalar_one_or_none()
    if orm_object is None:
        return None
    return BillPaymentDTO.model_validate(orm_object)


async def list_bill_payments(
    session: AsyncSession,
    bill_id: uuid.UUID,
    limit: int = 100,
    offset: int = 0,
) -> list[BillPaymentDTO]:
    result = await session.execute(
        select(BillPayment)
        .where(BillPayment.bill_id == bill_id)
        .order_by(BillPayment.executed_at.desc())
        .limit(limit)
        .offset(offset)
    )
    return [BillPaymentDTO.model_validate(row) for row in result.scalars().all()]
