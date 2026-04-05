import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.bills import service as bills_service


async def execute_bill(
    session: AsyncSession,
    bill_id: uuid.UUID,
) -> None:
    await bills_service.execute_bill(
        session=session,
        bill_id=bill_id,
        trigger="scheduled",
    )
