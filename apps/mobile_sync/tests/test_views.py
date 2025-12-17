from unittest import mock

from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from apps.mobile_sync.models import MobileDataSnapshot

User = get_user_model()


class MobileSnapshotViewTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="tester",
            email="tester@example.com",
            password="secret123",
        )
        self.client.force_authenticate(self.user)

    def test_get_snapshot_returns_cached_payload(self):
        snapshot = MobileDataSnapshot.objects.create(
            user=self.user,
            scope="all",
            payload={"user": {"id": self.user.id}},
            status=MobileDataSnapshot.Status.SUCCESS,
        )
        with mock.patch(
            "apps.mobile_sync.views.enqueue_snapshot_refresh",
            return_value=(snapshot, "task-123"),
        ):
            response = self.client.get(reverse("mobile_sync:snapshot"))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["queued_task_id"], "task-123")
        self.assertEqual(response.data["snapshot"]["payload"], snapshot.payload)

    def test_post_snapshot_queues_refresh(self):
        snapshot = MobileDataSnapshot.objects.create(
            user=self.user,
            scope="dashboard",
            status=MobileDataSnapshot.Status.PENDING,
        )
        with mock.patch(
            "apps.mobile_sync.views.enqueue_snapshot_refresh",
            return_value=(snapshot, "task-999"),
        ):
            response = self.client.post(
                reverse("mobile_sync:snapshot"),
                {"sections": ["dashboard"], "refresh": True},
                format="json",
            )

        self.assertEqual(response.status_code, status.HTTP_202_ACCEPTED)
        self.assertEqual(response.data["queued_task_id"], "task-999")
        self.assertIn("dashboard", response.data["sections"])

    def test_status_view_returns_404_for_unknown_scope(self):
        response = self.client.get(reverse("mobile_sync:snapshot-status", args=["missing"]))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_status_view_returns_existing_snapshot(self):
        snapshot = MobileDataSnapshot.objects.create(
            user=self.user,
            scope="all",
            payload={"meta": True},
            status=MobileDataSnapshot.Status.SUCCESS,
        )
        response = self.client.get(reverse("mobile_sync:snapshot-status", args=["all"]))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["payload"], snapshot.payload)
