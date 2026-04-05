import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock, patch

import pytest
from sqlalchemy import select

from app.bills import service
from app.bills.models import BillFrequency, BillPayment, BillPaymentStatus, BillStatus
from app.ledger.models import LedgerAccount
from app.outbox.models import OutboxEvent, OutboxEventType
from app.payees import service as payees_service
from app.payees.models import PayeeType
from app.payments.models import Payment
from shared.enums.currency import Currency
from shared.processors.base import PaymentIntent, PaymentProcessor, PaymentStatus
from shared.settings import EXPENSE_ACCOUNT_ID, LIABILITY_ACCOUNT_ID


@pytest.fixture
def mock_processor():
    processor = AsyncMock(spec=PaymentProcessor)
    processor.create_payment_intent.return_value = PaymentIntent(
        processor_id="pi_bill_test_123",
        client_secret="pi_bill_test_123_secret",
        status=PaymentStatus.PENDING,
        amount=7500,
        currency="usd",
        metadata={},
    )
    return processor


@pytest.fixture
async def ledger_accounts(session):
    expense = LedgerAccount(
        id=uuid.UUID(EXPENSE_ACCOUNT_ID),
        name="expenses",
        account_type="expense",
        currency=Currency.USD,
    )
    liability = LedgerAccount(
        id=uuid.UUID(LIABILITY_ACCOUNT_ID),
        name="liability",
        account_type="liability",
        currency=Currency.USD,
    )
    session.add_all([expense, liability])
    await session.flush()
    return expense, liability


@pytest.fixture
async def payee(session):
    return await payees_service.create_payee(
        session=session,
        name="Hydro One",
        payee_type=PayeeType.UTILITY,
        account_number="1234567890",
        routing_number="021000021",
        currency=Currency.USD,
    )


async def test_create_bill_schedules_outbox_event(session, payee):
    bill = await service.create_bill(
        session=session,
        payee_id=payee.id,
        card_id=None,
        amount=7500,
        currency=Currency.USD,
        frequency=BillFrequency.MONTHLY,
        next_due_date=datetime(2026, 4, 4, tzinfo=timezone.utc),
    )

    assert bill.id is not None
    assert bill.status == BillStatus.ACTIVE
    assert bill.frequency == BillFrequency.MONTHLY

    events = (
        (
            await session.execute(
                select(OutboxEvent).where(
                    OutboxEvent.event_type == OutboxEventType.BILL_SCHEDULED
                )
            )
        )
        .scalars()
        .all()
    )
    assert len(events) == 1
    assert events[0].payload["bill_id"] == str(bill.id)
    assert events[0].payload["payee_id"] == str(payee.id)


async def test_execute_bill_happy_path_creates_bill_payment_and_advances_due_date(
    session, payee, ledger_accounts, mock_processor
):
    bill = await service.create_bill(
        session=session,
        payee_id=payee.id,
        card_id=None,
        amount=7500,
        currency=Currency.USD,
        frequency=BillFrequency.MONTHLY,
        next_due_date=datetime(2026, 1, 31, tzinfo=timezone.utc),
    )

    with patch("app.bills.service.get_processor", return_value=mock_processor):
        execution = await service.execute_bill(
            session=session,
            bill_id=bill.id,
            trigger="manual",
        )

    assert execution.bill_payment.status == BillPaymentStatus.SUCCEEDED
    assert execution.bill_payment.payment_id is not None
    assert execution.bill.next_due_date == datetime(2026, 2, 28, tzinfo=timezone.utc)
    assert execution.bill.status == BillStatus.ACTIVE

    events = (
        (
            await session.execute(
                select(OutboxEvent).where(
                    OutboxEvent.event_type == OutboxEventType.BILL_EXECUTED
                )
            )
        )
        .scalars()
        .all()
    )
    assert len(events) == 1
    assert events[0].payload["bill_id"] == str(bill.id)


async def test_execute_bill_failure_records_failed_execution(
    session, payee, ledger_accounts, mock_processor
):
    bill = await service.create_bill(
        session=session,
        payee_id=payee.id,
        card_id=None,
        amount=7500,
        currency=Currency.USD,
        frequency=BillFrequency.WEEKLY,
        next_due_date=datetime(2026, 4, 4, tzinfo=timezone.utc),
    )
    mock_processor.create_payment_intent.side_effect = Exception("processor down")

    with patch("app.bills.service.get_processor", return_value=mock_processor):
        execution = await service.execute_bill(
            session=session,
            bill_id=bill.id,
            trigger="manual",
        )

    assert execution.bill_payment.status == BillPaymentStatus.FAILED
    assert execution.bill_payment.payment_id is None
    assert execution.bill.next_due_date == datetime(2026, 4, 4, tzinfo=timezone.utc)
    assert execution.bill.status == BillStatus.ACTIVE

    events = (
        (
            await session.execute(
                select(OutboxEvent).where(
                    OutboxEvent.event_type == OutboxEventType.BILL_FAILED
                )
            )
        )
        .scalars()
        .all()
    )
    assert len(events) == 1
    assert events[0].payload["bill_id"] == str(bill.id)


async def test_execute_bill_one_time_marks_completed(
    session, payee, ledger_accounts, mock_processor
):
    bill = await service.create_bill(
        session=session,
        payee_id=payee.id,
        card_id=None,
        amount=7500,
        currency=Currency.USD,
        frequency=BillFrequency.ONE_TIME,
        next_due_date=datetime(2026, 4, 4, tzinfo=timezone.utc),
    )

    with patch("app.bills.service.get_processor", return_value=mock_processor):
        execution = await service.execute_bill(
            session=session,
            bill_id=bill.id,
            trigger="manual",
        )

    assert execution.bill.status == BillStatus.COMPLETED
    assert execution.bill.next_due_date == datetime(2026, 4, 4, tzinfo=timezone.utc)
    assert execution.bill_payment.status == BillPaymentStatus.SUCCEEDED


async def test_manual_trigger_is_idempotent_for_completed_one_time_bill(
    session, payee, ledger_accounts, mock_processor
):
    bill = await service.create_bill(
        session=session,
        payee_id=payee.id,
        card_id=None,
        amount=7500,
        currency=Currency.USD,
        frequency=BillFrequency.ONE_TIME,
        next_due_date=datetime(2026, 4, 4, tzinfo=timezone.utc),
    )

    with patch("app.bills.service.get_processor", return_value=mock_processor):
        first = await service.execute_bill(
            session=session,
            bill_id=bill.id,
            trigger="manual",
        )
        second = await service.execute_bill(
            session=session, bill_id=bill.id, trigger="manual"
        )

    assert first.bill_payment.id == second.bill_payment.id
    assert first.bill_payment.payment_id == second.bill_payment.payment_id

    bill_payments = (await session.execute(select(BillPayment))).scalars().all()
    payments = (await session.execute(select(Payment))).scalars().all()
    assert len(bill_payments) == 1
    assert len(payments) == 1
