"""API endpoints that expose Celery-backed mobile snapshots."""

from __future__ import annotations

from typing import List

from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import MobileDataSnapshot
from .serializers import MobileSnapshotSerializer
from .services import MobileDataAssembler, normalize_scope
from .tasks import enqueue_snapshot_refresh


class MobileSnapshotView(APIView):
    """Return or queue a mobile snapshot for the authenticated user."""

    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs) -> Response:
        sections = self._parse_sections(request.query_params.get("sections"))
        force = self._coerce_bool(request.query_params.get("refresh"))
        snapshot, task_id = enqueue_snapshot_refresh(request.user, sections, force=force)
        serializer = MobileSnapshotSerializer(snapshot)
        response_status = status.HTTP_200_OK if snapshot.payload else status.HTTP_202_ACCEPTED
        return Response(
            {
                "snapshot": serializer.data,
                "queued_task_id": task_id,
                "scope": normalize_scope(sections),
                "sections": sections or list(MobileDataAssembler.ALL_SECTIONS),
            },
            status=response_status,
        )

    def post(self, request, *args, **kwargs) -> Response:
        sections = request.data.get("sections") or request.data.get("scope")
        if isinstance(sections, str):
            section_list = self._parse_sections(sections)
        elif isinstance(sections, list):
            section_list = [section for section in sections if isinstance(section, str)]
        else:
            section_list = None
        force = self._coerce_bool(request.data.get("refresh", True))
        snapshot, task_id = enqueue_snapshot_refresh(request.user, section_list, force=force)
        serializer = MobileSnapshotSerializer(snapshot)
        return Response(
            {
                "snapshot": serializer.data,
                "queued_task_id": task_id,
                "scope": normalize_scope(section_list),
                "sections": section_list or list(MobileDataAssembler.ALL_SECTIONS),
            },
            status=status.HTTP_202_ACCEPTED,
        )

    def _parse_sections(self, raw_sections: str | List[str] | None) -> List[str] | None:
        if raw_sections is None:
            return None
        if isinstance(raw_sections, list):
            items = raw_sections
        else:
            items = [section.strip() for section in raw_sections.split(",") if section.strip()]
        filtered = [section for section in items if section in MobileDataAssembler.ALL_SECTIONS]
        return filtered or None

    @staticmethod
    def _coerce_bool(value) -> bool:
        if isinstance(value, bool):
            return value
        if value is None:
            return False
        value_str = str(value).strip().lower()
        return value_str in {"1", "true", "yes", "y", "on"}


class MobileSnapshotStatusView(APIView):
    """Fetch the latest status for a stored snapshot."""

    permission_classes = [IsAuthenticated]

    def get(self, request, scope: str, *args, **kwargs) -> Response:
        snapshot = MobileDataSnapshot.objects.filter(
            user=request.user,
            scope=scope,
        ).first()
        if not snapshot:
            return Response({"detail": "Snapshot not found"}, status=status.HTTP_404_NOT_FOUND)
        serializer = MobileSnapshotSerializer(snapshot)
        return Response(serializer.data)
