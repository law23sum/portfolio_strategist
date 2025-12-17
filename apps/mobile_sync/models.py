"""Models for mobile data synchronization."""

from __future__ import annotations

from django.conf import settings
from django.db import models
from django.utils import timezone


class MobileDataSnapshot(models.Model):
    """Stores a serialized snapshot of the user's data for mobile clients."""

    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        RUNNING = "running", "Running"
        SUCCESS = "success", "Success"
        FAILED = "failed", "Failed"

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="mobile_snapshots",
    )
    scope = models.CharField(
        max_length=64,
        help_text="Normalized scope key describing which sections are included (e.g. 'all', 'dashboard+records').",
    )
    payload = models.JSONField(default=dict, blank=True)
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
    )
    task_id = models.CharField(max_length=255, blank=True)
    error_message = models.TextField(blank=True)
    last_synced_at = models.DateTimeField(null=True, blank=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("user", "scope")
        ordering = ["-updated_at"]

    def __str__(self) -> str:  # pragma: no cover - human readable
        return f"Snapshot({self.user_id}, scope={self.scope}, status={self.status})"

    def mark_running(self, task_id: str | None = None) -> None:
        self.status = self.Status.RUNNING
        if task_id:
            self.task_id = task_id
        self.error_message = ""
        self.save(update_fields=["status", "task_id", "error_message", "updated_at"])

    def mark_success(self, payload: dict, ttl_seconds: int) -> None:
        now = timezone.now()
        self.payload = payload
        self.status = self.Status.SUCCESS
        self.last_synced_at = now
        self.expires_at = now + timezone.timedelta(seconds=ttl_seconds)
        self.error_message = ""
        self.save(
            update_fields=[
                "payload",
                "status",
                "last_synced_at",
                "expires_at",
                "error_message",
                "updated_at",
            ]
        )

    def mark_failed(self, message: str) -> None:
        self.status = self.Status.FAILED
        self.error_message = message[:2000]
        self.save(update_fields=["status", "error_message", "updated_at"])

    def is_expired(self) -> bool:
        return bool(self.expires_at and self.expires_at <= timezone.now())

    @property
    def is_successful(self) -> bool:
        return self.status == self.Status.SUCCESS
