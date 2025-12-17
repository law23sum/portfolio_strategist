from django.contrib import admin

from .models import MobileDataSnapshot


@admin.register(MobileDataSnapshot)
class MobileDataSnapshotAdmin(admin.ModelAdmin):
    list_display = ("user", "scope", "status", "last_synced_at", "expires_at")
    list_filter = ("status", "scope")
    search_fields = ("user__email", "user__username", "scope", "task_id")
    readonly_fields = ("created_at", "updated_at", "last_synced_at", "expires_at", "task_id")
