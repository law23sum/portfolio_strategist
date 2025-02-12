import logging
import time

from celery import shared_task
from celery_progress.backend import ProgressRecorder
from django.utils import timezone

logger = logging.getLogger("pegasus.examples")


@shared_task(bind=True)
def progress_bar_task(self, seconds):
    progress_recorder = ProgressRecorder(self)
    count = seconds * 10
    for i in range(count):
        time.sleep(0.1)
        progress_recorder.set_progress(i + 1, count)
    return "done"


@shared_task
def example_log_task():
    logger.info(f"The current system time is {timezone.now()}")
