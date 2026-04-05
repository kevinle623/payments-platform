import calendar
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.bills import repository
from app.bills.models import BillFrequency, BillPaymentStatus, BillStatus
from app.bills.schemas import BillDetailResponse, BillDTO, BillExecutionResponse
from app.outbox import service as outbox_service
from app.outbox.models import OutboxEventType
from app.payees import service as payees_service
from app.payments import service as payments_service
from app.payments.schemas import AuthorizeRequest
from shared.enums.currency import Currency
from shared.exceptions import PaymentNotFoundError
from shared.logger import get_logger
from shared.processors.factory import get_processor
from shared.settings import EXPENSE_ACCOUNT_ID, LIABILITY_ACCOUNT_ID

logger = get_logger(__name__)

_MANUAL_TRIGGER = "manual"


def _advance_due_date(next_due_date: datetime, frequency: BillFrequency) -> datetime:
    if frequency == BillFrequency.WEEKLY:
        return next_due_date + timedelta(days=7)

    if frequency == BillFrequency.BIWEEKLY:
        return next_due_date + timedelta(days=14)

    if frequency == BillFrequency.MONTHLY:
        month_index = next_due_date.month
        year = next_due_date.year + month_index // 12
        month = month_index % 12 + 1
        day = min(next_due_date.day, calendar.monthrange(year, month)[1])
        return next_due_date.replace(year=year, month=month, day=day)

    return next_due_date


def _execution_idempotency_key(bill_id: uuid.UUID, due_date: datetime) -> str:
    return f"bill:{bill_id}:{due_date.isoformat()}"


async def create_bill(
    session: AsyncSession,
    payee_id: uuid.UUID,
    card_id: uuid.UUID | None,
    amount: int,
    currency: str,
    frequency: BillFrequency,
    next_due_date: datetime,
) -> BillDTO:
    await payees_service.get_payee(session, payee_id)

    try:
        bill = await repository.create_bill(
            session=session,
            payee_id=payee_id,
            card_id=card_id,
            amount=amount,
            currency=currency,
            frequency=frequency,
            next_due_date=next_due_date,
            status=BillStatus.ACTIVE,
        )
        await outbox_service.publish_event(
            session,
            event_type=OutboxEventType.BILL_SCHEDULED,
            payload={
                "bill_id": str(bill.id),
                "payee_id": str(bill.payee_id),
                "card_id": str(bill.card_id) if bill.card_id else None,
                "amount": bill.amount,
                "currency": bill.currency,
                "frequency": bill.frequency,
                "next_due_date": bill.next_due_date.isoformat(),
            },
        )
        await session.commit()
        logger.info(
            "bill scheduled | bill_id=%s payee_id=%s amount=%d frequency=%s next_due_date=%s",
            bill.id,
            bill.payee_id,
            bill.amount,
            bill.frequency,
            bill.next_due_date,
        )
        return bill
    except Exception:
        await session.rollback()
        raise


async def list_bills(
    session: AsyncSession,
    status: BillStatus | None = None,
    limit: int = 100,
    offset: int = 0,
) -> list[BillDTO]:
    return await repository.list_bills(
        session=session, status=status, limit=limit, offset=offset
    )


async def get_bill_detail(
    session: AsyncSession,
    bill_id: uuid.UUID,
) -> BillDetailResponse:
    bill = await repository.get_bill(session, bill_id)
    if bill is None:
        raise PaymentNotFoundError(f"Bill not found: {bill_id}")
    payments = await repository.list_bill_payments(session, bill_id)
    return BillDetailResponse(bill=bill, payments=payments)


async def update_bill(
    session: AsyncSession,
    bill_id: uuid.UUID,
    updates: dict[str, Any],
) -> BillDTO:
    if not updates:
        bill = await repository.get_bill(session, bill_id)
        if bill is None:
            raise PaymentNotFoundError(f"Bill not found: {bill_id}")
        return bill

    try:
        updated = await repository.update_bill(session, bill_id, updates=updates)
        if updated is None:
            raise PaymentNotFoundError(f"Bill not found: {bill_id}")
        await session.commit()
        logger.info("bill updated | bill_id=%s updates=%s", bill_id, updates)
        return updated
    except Exception:
        await session.rollback()
        raise


async def execute_bill(
    session: AsyncSession,
    bill_id: uuid.UUID,
    trigger: str = _MANUAL_TRIGGER,
) -> BillExecutionResponse:
    bill = await repository.get_bill(session, bill_id)
    if bill is None:
        raise PaymentNotFoundError(f"Bill not found: {bill_id}")

    latest_execution = await repository.get_latest_bill_payment(session, bill_id)
    if bill.status == BillStatus.COMPLETED and latest_execution is not None:
        logger.info(
            "bill already completed, returning latest execution | bill_id=%s bill_payment_id=%s",
            bill_id,
            latest_execution.id,
        )
        return BillExecutionResponse(bill=bill, bill_payment=latest_execution)

    now = datetime.now(timezone.utc)
    if (
        trigger == _MANUAL_TRIGGER
        and bill.next_due_date > now
        and latest_execution is not None
        and latest_execution.status == BillPaymentStatus.SUCCEEDED
    ):
        logger.info(
            (
                "bill manual idempotency hit, returning latest execution | "
                "bill_id=%s bill_payment_id=%s"
            ),
            bill_id,
            latest_execution.id,
        )
        return BillExecutionResponse(bill=bill, bill_payment=latest_execution)

    try:
        response = await payments_service.authorize(
            session=session,
            request=AuthorizeRequest(
                amount=bill.amount,
                currency=Currency(bill.currency),
                idempotency_key=_execution_idempotency_key(bill.id, bill.next_due_date),
                metadata={
                    "bill_id": str(bill.id),
                    "payee_id": str(bill.payee_id),
                    "trigger": trigger,
                },
                card_id=bill.card_id,
            ),
            processor=get_processor(),
            expense_account_id=uuid.UUID(EXPENSE_ACCOUNT_ID),
            liability_account_id=uuid.UUID(LIABILITY_ACCOUNT_ID),
        )

        existing = await repository.get_bill_payment_by_bill_and_payment(
            session=session,
            bill_id=bill.id,
            payment_id=response.id,
        )
        if existing is not None:
            current_bill = await repository.get_bill(session, bill.id)
            return BillExecutionResponse(
                bill=current_bill if current_bill is not None else bill,
                bill_payment=existing,
            )

        bill_payment = await repository.create_bill_payment(
            session=session,
            bill_id=bill.id,
            payment_id=response.id,
            status=BillPaymentStatus.SUCCEEDED,
        )

        updates: dict[str, Any] = {}
        if bill.frequency == BillFrequency.ONE_TIME:
            updates["status"] = BillStatus.COMPLETED
        else:
            updates["next_due_date"] = _advance_due_date(
                bill.next_due_date, bill.frequency
            )
            updates["status"] = BillStatus.ACTIVE

        updated_bill = await repository.update_bill(session, bill.id, updates=updates)
        if updated_bill is None:
            raise PaymentNotFoundError(f"Bill not found: {bill.id}")

        await outbox_service.publish_event(
            session,
            event_type=OutboxEventType.BILL_EXECUTED,
            payload={
                "bill_id": str(updated_bill.id),
                "bill_payment_id": str(bill_payment.id),
                "payment_id": str(response.id),
                "amount": updated_bill.amount,
                "currency": updated_bill.currency,
                "trigger": trigger,
                "next_due_date": updated_bill.next_due_date.isoformat(),
            },
        )
        await session.commit()
        logger.info(
            "bill executed | bill_id=%s bill_payment_id=%s payment_id=%s trigger=%s",
            updated_bill.id,
            bill_payment.id,
            response.id,
            trigger,
        )
        return BillExecutionResponse(bill=updated_bill, bill_payment=bill_payment)
    except Exception as exc:
        await session.rollback()
        logger.warning(
            "bill execution failed | bill_id=%s trigger=%s error=%s",
            bill_id,
            trigger,
            str(exc),
        )
        return await _record_failed_execution(
            session=session,
            bill=bill,
            trigger=trigger,
            error=str(exc),
        )


async def _record_failed_execution(
    session: AsyncSession,
    bill: BillDTO,
    trigger: str,
    error: str,
) -> BillExecutionResponse:
    try:
        failed_payment = await repository.create_bill_payment(
            session=session,
            bill_id=bill.id,
            payment_id=None,
            status=BillPaymentStatus.FAILED,
        )
        await outbox_service.publish_event(
            session,
            event_type=OutboxEventType.BILL_FAILED,
            payload={
                "bill_id": str(bill.id),
                "bill_payment_id": str(failed_payment.id),
                "amount": bill.amount,
                "currency": bill.currency,
                "trigger": trigger,
                "error": error,
            },
        )
        await session.commit()
        current_bill = await repository.get_bill(session, bill.id)
        return BillExecutionResponse(
            bill=current_bill if current_bill is not None else bill,
            bill_payment=failed_payment,
        )
    except Exception:
        await session.rollback()
        raise
