"""Serializers for mobile sync endpoints."""

from rest_framework import serializers

from .models import MobileDataSnapshot


class MobileSnapshotSerializer(serializers.ModelSerializer):
    is_stale = serializers.SerializerMethodField()

    class Meta:
        model = MobileDataSnapshot
        fields = (
            "id",
            "scope",
            "status",
            "payload",
            "last_synced_at",
            "expires_at",
            "task_id",
            "error_message",
            "is_stale",
        )
        read_only_fields = fields

    def get_is_stale(self, obj: MobileDataSnapshot) -> bool:
        return obj.is_expired()
