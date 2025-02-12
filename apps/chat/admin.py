from django.contrib import admin

from .models import Chat, ChatMessage


@admin.register(Chat)
class ChatAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "name")
    search_fields = ("user__username", "name")
    list_filter = ("user",)


@admin.register(ChatMessage)
class ChatMessageAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "chat",
        "created_at",
        "message_type",
        "short_content",
    )
    search_fields = ("chat__name", "message_type", "content")
    list_filter = (
        "chat",
        "message_type",
        "created_at",
    )

    def short_content(self, obj):
        return obj.content[:50]
