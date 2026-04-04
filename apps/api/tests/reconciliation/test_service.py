import uuid

import pytest

from app.reconciliation import repository, service
from app.reconciliation.schemas import (
    ReconciliationDiscrepancyDTO,
    ReconciliationRunDTO,
)

# -- runs --


async def test_create_run(session):
    run = await repository.create_run(session)

    assert isinstance(run, ReconciliationRunDTO)
    assert run.id is not None
    assert run.started_at is not None
    assert run.completed_at is None
    assert run.checked == 0
    assert run.mismatches == 0


async def test_complete_run(session):
    run = await repository.create_run(session)

    completed = await repository.complete_run(
        session, run_id=run.id, checked=10, mismatches=2
    )

    assert completed.id == run.id
    assert completed.completed_at is not None
    assert completed.checked == 10
    assert completed.mismatches == 2


async def test_complete_run_not_found_returns_none(session):
    result = await repository.complete_run(
        session, run_id=uuid.uuid4(), checked=5, mismatches=0
    )
    assert result is None


async def test_list_runs_empty(session):
    runs = await service.list_runs(session=session)
    assert runs == []


async def test_list_runs_returns_all_ordered_desc(session):
    run_a = await repository.create_run(session)
    run_b = await repository.create_run(session)

    runs = await service.list_runs(session=session)

    assert len(runs) == 2
    # most recent first -- run_b was created after run_a
    run_ids = [r.id for r in runs]
    assert run_ids.index(run_b.id) < run_ids.index(run_a.id)


async def test_list_runs_pagination(session):
    for _ in range(5):
        await repository.create_run(session)

    page1 = await service.list_runs(session=session, limit=3, offset=0)
    page2 = await service.list_runs(session=session, limit=3, offset=3)

    assert len(page1) == 3
    assert len(page2) == 2
    assert {r.id for r in page1}.isdisjoint({r.id for r in page2})


# -- discrepancies --


async def test_create_discrepancy(session):
    run = await repository.create_run(session)
    payment_id = uuid.uuid4()

    discrepancy = await repository.create_discrepancy(
        session,
        run_id=run.id,
        payment_id=payment_id,
        processor_payment_id="pi_test_123",
        our_status="succeeded",
        stripe_status="requires_capture",
    )

    assert isinstance(discrepancy, ReconciliationDiscrepancyDTO)
    assert discrepancy.run_id == run.id
    assert discrepancy.payment_id == payment_id
    assert discrepancy.our_status == "succeeded"
    assert discrepancy.stripe_status == "requires_capture"
    assert discrepancy.detected_at is not None


async def test_list_discrepancies_empty(session):
    discrepancies = await service.list_discrepancies(session=session)
    assert discrepancies == []


async def test_list_discrepancies_returns_all(session):
    run = await repository.create_run(session)

    for _ in range(3):
        await repository.create_discrepancy(
            session,
            run_id=run.id,
            payment_id=uuid.uuid4(),
            processor_payment_id=f"pi_{uuid.uuid4().hex[:8]}",
            our_status="succeeded",
            stripe_status="requires_capture",
        )

    discrepancies = await service.list_discrepancies(session=session)
    assert len(discrepancies) == 3


async def test_list_discrepancies_filter_by_run_id(session):
    run_a = await repository.create_run(session)
    run_b = await repository.create_run(session)

    await repository.create_discrepancy(
        session,
        run_id=run_a.id,
        payment_id=uuid.uuid4(),
        processor_payment_id="pi_aaa",
        our_status="succeeded",
        stripe_status="canceled",
    )
    await repository.create_discrepancy(
        session,
        run_id=run_a.id,
        payment_id=uuid.uuid4(),
        processor_payment_id="pi_bbb",
        our_status="succeeded",
        stripe_status="requires_capture",
    )
    await repository.create_discrepancy(
        session,
        run_id=run_b.id,
        payment_id=uuid.uuid4(),
        processor_payment_id="pi_ccc",
        our_status="succeeded",
        stripe_status="canceled",
    )

    run_a_discrepancies = await service.list_discrepancies(
        session=session, run_id=run_a.id
    )
    assert len(run_a_discrepancies) == 2
    assert all(d.run_id == run_a.id for d in run_a_discrepancies)

    run_b_discrepancies = await service.list_discrepancies(
        session=session, run_id=run_b.id
    )
    assert len(run_b_discrepancies) == 1
    assert run_b_discrepancies[0].run_id == run_b.id


async def test_list_discrepancies_pagination(session):
    run = await repository.create_run(session)

    for _ in range(5):
        await repository.create_discrepancy(
            session,
            run_id=run.id,
            payment_id=uuid.uuid4(),
            processor_payment_id=f"pi_{uuid.uuid4().hex[:8]}",
            our_status="succeeded",
            stripe_status="canceled",
        )

    page1 = await service.list_discrepancies(session=session, limit=3, offset=0)
    page2 = await service.list_discrepancies(session=session, limit=3, offset=3)

    assert len(page1) == 3
    assert len(page2) == 2
    assert {d.id for d in page1}.isdisjoint({d.id for d in page2})


# -- full run lifecycle --


async def test_full_run_lifecycle(session):
    run = await repository.create_run(session)
    assert run.completed_at is None

    payment_ids = [uuid.uuid4() for _ in range(3)]
    for i, payment_id in enumerate(payment_ids):
        await repository.create_discrepancy(
            session,
            run_id=run.id,
            payment_id=payment_id,
            processor_payment_id=f"pi_{i}",
            our_status="succeeded",
            stripe_status="requires_capture",
        )

    completed = await repository.complete_run(
        session, run_id=run.id, checked=10, mismatches=3
    )

    assert completed.completed_at is not None
    assert completed.checked == 10
    assert completed.mismatches == 3

    discrepancies = await service.list_discrepancies(session=session, run_id=run.id)
    assert len(discrepancies) == 3
