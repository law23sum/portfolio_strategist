from rest_framework import serializers

from .models import Chat, ChatMessage


class ChatMessageSerializer(serializers.ModelSerializer):
    attachment_url = serializers.SerializerMethodField()

    class Meta:
        model = ChatMessage
        fields = (
            "id",
            "chat",
            "message_type",
            "content",
            "created_at",
            "attachment",
            "attachment_type",
            "attachment_url",
        )
        read_only_fields = ("id", "created_at", "attachment_url")

    def get_attachment_url(self, obj):
        if obj.attachment:
            request = self.context.get("request")
            if request:
                return request.build_absolute_uri(obj.attachment.url)
            return obj.attachment.url
        return None


class ChatSerializer(serializers.ModelSerializer):
    """
    Basic serializer for Chats.
    """

    messages = ChatMessageSerializer(many=True, read_only=True)

    class Meta:
        model = Chat
        fields = ("id", "name", "messages")
