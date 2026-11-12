from celery import Celery

celery_app = Celery(
    "online-cinema",
    broker="redis://localhost:6379/0",
    include=["tasks.accounts"],
)

celery_app.conf.update(
    timezone="UTC",
    beat_schedule={
        "delete-expired-activation-tokens-every-15-minutes": {
            "task": "tasks.accounts.delete_expired_activation_tokens",
            "schedule": 900.0,
        },
    },
)
