from celery import Celery

from shared.settings import RABBITMQ_URL

celery_app = Celery(
    "payments_platform",
    broker=RABBITMQ_URL,
    include=[
        "workers.producers.payments.outbox_poller",
        "workers.jobs.payments.reconciliation",
    ],
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    timezone="UTC",
    enable_utc=True,
    beat_schedule={
        "poll-outbox": {
            "task": "workers.producers.payments.outbox_poller.poll_and_publish",
            "schedule": 10.0,  # every 10 seconds
        },
        "reconcile-payments": {
            "task": "workers.jobs.payments.reconciliation.run_reconciliation",
            "schedule": 86400.0,  # every 24 hours
        },
    },
)
