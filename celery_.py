import os

from celery import Celery

broker_url = "redis://redis:6379/0"

app = Celery("tasks", broker=broker_url)

app.conf.update(
    result_backend="redis://localhost:6379/0",
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
)
