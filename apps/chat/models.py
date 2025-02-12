from typing import Dict, List

from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _

from apps.utils.models import BaseModel


class MessageTypes(models.TextChoices):
    HUMAN = "HUMAN", _("Human")
    AI = "AI", _("AI")
    SYSTEM = "SYSTEM", _("System")


class Chat(BaseModel):
    """
    A chat (session) instance.
    """

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True, blank=True, related_name="chats"
    )
    name = models.CharField(max_length=100, default="Unnamed Chat")

    def __str__(self):
        return f"{self.name} ({self.user})"

    def get_openai_messages(self) -> List[Dict]:
        """
        Return a list of messages ready to pass to the OpenAI ChatCompletion API.
        """
        return [m.to_openai_dict() for m in self.messages.all()]


class ChatMessage(BaseModel):
    """
    A message in a Chat.
    """

    chat = models.ForeignKey(Chat, on_delete=models.CASCADE, related_name="messages")
    message_type = models.CharField(max_length=10, choices=MessageTypes.choices)
    content = models.TextField()

    class Meta:
        ordering = ["created_at"]

    @property
    def is_ai_message(self) -> bool:
        return self.message_type == MessageTypes.AI

    @property
    def is_human_message(self) -> bool:
        return self.message_type == MessageTypes.HUMAN

    def to_openai_dict(self) -> Dict:
        return {
            "role": self.get_openai_role(),
            "content": self.content,
        }

    def get_openai_role(self):
        if self.message_type == MessageTypes.HUMAN:
            return "user"
        elif self.message_type == MessageTypes.AI:
            return "assistant"
        else:
            return "system"
