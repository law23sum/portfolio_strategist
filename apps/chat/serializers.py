from rest_framework import serializers

from .models import Chat, ChatMessage


class ChatMessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ChatMessage
        fields = ("id", "chat", "message_type", "content", "created_at")


class ChatSerializer(serializers.ModelSerializer):
    """
    Basic serializer for Chats.
    """

    messages = ChatMessageSerializer(many=True)

    class Meta:
        model = Chat
        fields = ("id", "name", "messages")
