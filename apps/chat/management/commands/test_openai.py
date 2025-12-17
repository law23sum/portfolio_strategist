from django.conf import settings
from django.core.management.base import BaseCommand

from apps.chat.utils import test_openai_connection


class Command(BaseCommand):
    help = "Test the OpenAI API key connection and configuration."

    def handle(self, *args, **options):
        self.stdout.write("Testing OpenAI API connection...")
        self.stdout.write(f"Model: {settings.AI_CHAT_OPENAI_MODEL}")
        self.stdout.write(f"API Key: {'*' * 20 if settings.AI_CHAT_OPENAI_API_KEY else 'NOT SET'}")
        self.stdout.write("")

        success, result = test_openai_connection()

        if success:
            self.stdout.write(self.style.SUCCESS("✓ OpenAI API connection successful!"))
            self.stdout.write(f"Response: {result}")
        else:
            self.stdout.write(self.style.ERROR("✗ OpenAI API connection failed!"))
            self.stdout.write(self.style.ERROR(f"Error: {result}"))
            self.stdout.write("")
            self.stdout.write("Please check:")
            self.stdout.write("1. That AI_CHAT_OPENAI_API_KEY is set in your environment or .env file")
            self.stdout.write("2. That the API key is valid and has sufficient credits")
            self.stdout.write("3. That your network connection is working")
