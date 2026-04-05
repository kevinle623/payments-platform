from datetime import datetime, timezone

from app.bills import repository as bills_repository
from app.bills import service as bills_service
from app.bills.models import BillFrequency, BillStatus
from app.payees import service as payees_service
from app.payees.models import PayeeType
from shared.enums.currency import Currency


async def test_get_due_bills_returns_only_active_due_bills(session):
    payee = await payees_service.create_payee(
        session=session,
        name="Utility",
        payee_type=PayeeType.UTILITY,
        account_number="1234567890",
        routing_number="021000021",
        currency=Currency.USD,
    )

    due_active = await bills_service.create_bill(
        session=session,
        payee_id=payee.id,
        card_id=None,
        amount=2500,
        currency=Currency.USD,
        frequency=BillFrequency.MONTHLY,
        next_due_date=datetime(2026, 4, 4, tzinfo=timezone.utc),
    )
    future_active = await bills_service.create_bill(
        session=session,
        payee_id=payee.id,
        card_id=None,
        amount=2600,
        currency=Currency.USD,
        frequency=BillFrequency.MONTHLY,
        next_due_date=datetime(2026, 4, 20, tzinfo=timezone.utc),
    )
    due_paused = await bills_service.create_bill(
        session=session,
        payee_id=payee.id,
        card_id=None,
        amount=2700,
        currency=Currency.USD,
        frequency=BillFrequency.MONTHLY,
        next_due_date=datetime(2026, 4, 4, tzinfo=timezone.utc),
    )
    due_completed = await bills_service.create_bill(
        session=session,
        payee_id=payee.id,
        card_id=None,
        amount=2800,
        currency=Currency.USD,
        frequency=BillFrequency.ONE_TIME,
        next_due_date=datetime(2026, 4, 4, tzinfo=timezone.utc),
    )

    await bills_service.update_bill(
        session=session,
        bill_id=due_paused.id,
        updates={"status": BillStatus.PAUSED},
    )
    await bills_service.update_bill(
        session=session,
        bill_id=due_completed.id,
        updates={"status": BillStatus.COMPLETED},
    )

    due_bills = await bills_repository.get_due_bills(
        session,
        now=datetime(2026, 4, 5, tzinfo=timezone.utc),
    )
    due_bill_ids = {bill.id for bill in due_bills}

    assert due_active.id in due_bill_ids
    assert future_active.id not in due_bill_ids
    assert due_paused.id not in due_bill_ids
    assert due_completed.id not in due_bill_ids
