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
        Return a list of messages ready to pass to the OpenInvestment & RetirementCompletion API.
        """
        return [m.to_openai_dict() for m in self.messages.all()]


class ChatMessage(BaseModel):
    """
    A message in a Chat.
    """

    chat = models.ForeignKey(Chat, on_delete=models.CASCADE, related_name="messages")
    message_type = models.CharField(max_length=10, choices=MessageTypes.choices)
    content = models.TextField()
    attachment = models.FileField(upload_to="chat_attachments/", blank=True, null=True)
    attachment_type = models.CharField(max_length=50, blank=True, help_text="Type of attachment: image, csv, pdf, etc.")

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


class AICredential(models.Model):
    """API keys for AI providers (OpenAI, Anthropic, Google, xAI, Cursor IDE)."""

    PROVIDER_OPENAI = "openai"
    PROVIDER_ANTHROPIC = "anthropic"
    PROVIDER_GOOGLE = "google"
    PROVIDER_XAI = "xai"
    PROVIDER_CURSOR = "cursor"
    PROVIDER_CHOICES = (
        (PROVIDER_OPENAI, "OpenAI (GPT)"),
        (PROVIDER_ANTHROPIC, "Anthropic (Claude)"),
        (PROVIDER_GOOGLE, "Google (Gemini)"),
        (PROVIDER_XAI, "xAI (Grok)"),
        (PROVIDER_CURSOR, "Cursor IDE"),
    )

    provider = models.CharField(max_length=50, choices=PROVIDER_CHOICES, unique=True)
    label = models.CharField(max_length=128, blank=True, help_text="Optional note to help identify this key")
    api_key = models.CharField(max_length=512)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "AI Credential"
        verbose_name_plural = "AI Credentials"
        ordering = ["provider"]

    def __str__(self):
        label = self.label or dict(self.PROVIDER_CHOICES).get(self.provider, self.provider)
        return f"{label} ({'active' if self.is_active else 'inactive'})"
