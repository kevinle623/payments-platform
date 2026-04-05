from celery import Celery

from shared.settings import RABBITMQ_URL

celery_app = Celery(
    "payments_platform",
    broker=RABBITMQ_URL,
    include=[
        "workers.producers.outbox_poller",
        "workers.jobs.bills.scheduler",
        "workers.jobs.payments.reconciliation",
        "workers.jobs.issuer.hold_expiry",
    ],
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    timezone="UTC",
    enable_utc=True,
    beat_schedule={
        "poll-outbox": {
            "task": "workers.producers.outbox_poller.poll_and_publish",
            "schedule": 10.0,  # every 10 seconds
        },
        "reconcile-payments": {
            "task": "workers.jobs.payments.reconciliation.run_reconciliation",
            "schedule": 86400.0,  # every 24 hours
        },
        "expire-stale-holds": {
            "task": "workers.jobs.issuer.hold_expiry.run_hold_expiry",
            "schedule": 3600.0,  # every hour
        },
        "schedule-bills": {
            "task": "workers.jobs.bills.scheduler.run_bill_scheduler",
            "schedule": 300.0,  # every 5 minutes
        },
    },
)
