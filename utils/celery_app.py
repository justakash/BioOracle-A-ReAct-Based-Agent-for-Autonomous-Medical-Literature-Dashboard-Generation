"""
Celery Task Queue Configuration
Used for background pipeline execution and scheduled report delivery.
"""

import os

from celery import Celery
from loguru import logger

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

celery_app = Celery(
    "biooracle",
    broker=REDIS_URL,
    backend=REDIS_URL,
    include=["utils.tasks"],
)

celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="UTC",
    enable_utc=True,
    task_soft_time_limit=300,
    task_time_limit=600,
    worker_prefetch_multiplier=1,
)

logger.info("Celery app configured.")
