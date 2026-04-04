from celery import Celery

from shared.settings import RABBITMQ_URL

celery_app = Celery("payments_platform", broker=RABBITMQ_URL, include=["workers.outbox_poller"])

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    timezone="UTC",
    enable_utc=True,
    beat_schedule={
        "poll-outbox": {
            "task": "workers.outbox_poller.poll_and_publish",
            "schedule": 10.0,  # every 10 seconds
        },
    },
)
