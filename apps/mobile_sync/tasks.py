"""Celery tasks for generating mobile snapshots."""

from __future__ import annotations

import logging
from typing import Iterable

from celery import shared_task
from django.conf import settings
from django.contrib.auth import get_user_model

from .models import MobileDataSnapshot
from .services import MobileDataAssembler, normalize_scope

logger = logging.getLogger(__name__)
User = get_user_model()


def _get_snapshot(user: User, scope: str) -> MobileDataSnapshot:
    snapshot, _ = MobileDataSnapshot.objects.get_or_create(user=user, scope=scope)
    return snapshot


@shared_task(bind=True, autoretry_for=(Exception,), retry_backoff=15, retry_kwargs={"max_retries": 3})
def generate_mobile_snapshot(self, user_id: int, sections: Iterable[str] | None = None) -> dict:
    """Generate a serialized snapshot for the given user."""

    user = User.objects.get(pk=user_id)
    normalized_scope = normalize_scope(sections)
    snapshot = _get_snapshot(user, normalized_scope)

    try:
        snapshot.mark_running(task_id=self.request.id)
        assembler = MobileDataAssembler(user=user)
        payload = assembler.build_payload(sections)
        ttl_seconds = getattr(settings, "MOBILE_SYNC_TTL_SECONDS", 900)
        snapshot.mark_success(payload, ttl_seconds=ttl_seconds)
        logger.info("Generated mobile snapshot for user=%s scope=%s", user.id, normalized_scope)
        return {"snapshot_id": snapshot.id, "scope": normalized_scope}
    except Exception as exc:
        logger.exception("Failed generating mobile snapshot for user=%s scope=%s", user.id, normalized_scope)
        snapshot.mark_failed(str(exc))
        raise exc


def enqueue_snapshot_refresh(
    user: User, sections: Iterable[str] | None = None, force: bool = False
) -> tuple[MobileDataSnapshot, str | None]:
    """Helper to queue a background refresh if one is needed."""

    normalized_scope = normalize_scope(sections)
    snapshot = _get_snapshot(user, normalized_scope)
    needs_refresh = (
        force or snapshot.status == MobileDataSnapshot.Status.FAILED or snapshot.is_expired() or not snapshot.payload
    )

    task_id = None
    if needs_refresh:
        task = generate_mobile_snapshot.delay(user.id, list(sections or MobileDataAssembler.ALL_SECTIONS))
        task_id = task.id
        snapshot.status = MobileDataSnapshot.Status.PENDING
        snapshot.task_id = task_id
        snapshot.save(update_fields=["status", "task_id", "updated_at"])

    return snapshot, task_id
