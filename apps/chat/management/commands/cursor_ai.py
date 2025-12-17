"""
Management command for Cursor AI - Multi-Provider Chat Interface

This command provides an interactive interface to chat with various AI providers.
API keys are retrieved from the database (AICredential model) or environment variables.
"""

from django.conf import settings
from django.core.management.base import BaseCommand

from apps.chat.utils import get_ai_api_key


class Command(BaseCommand):
    help = "Cursor AI - Multi-Provider Chat Interface"

    def add_arguments(self, parser):
        parser.add_argument(
            "--provider",
            type=str,
            help="AI provider to use (openai, anthropic, google, xai, cursor)",
        )

    def handle(self, *args, **options):
        providers = [
            {
                "id": "1",
                "name": "OpenAI (GPT)",
                "key": "openai",
                "module": "openai",
            },
            {
                "id": "2",
                "name": "Anthropic (Claude)",
                "key": "anthropic",
                "module": "anthropic",
            },
            {
                "id": "3",
                "name": "Google (Gemini)",
                "key": "google",
                "module": "google",
            },
            {
                "id": "4",
                "name": "xAI (Grok)",
                "key": "xai",
                "module": "xai",
            },
            {
                "id": "5",
                "name": "Cursor IDE",
                "key": "cursor",
                "module": "cursor",
            },
        ]

        # Check availability of each provider
        available_providers = []
        for provider in providers:
            api_key = get_ai_api_key(provider["key"])
            provider["available"] = api_key is not None
            provider["api_key"] = api_key
            if provider["available"]:
                available_providers.append(provider)

        # Display header
        self.stdout.write("")
        self.stdout.write("=" * 70)
        self.stdout.write("  Cursor AI - Multi-Provider Chat Interface")
        self.stdout.write("=" * 70)
        self.stdout.write("")
        self.stdout.write("Available AI Providers:")
        self.stdout.write("-" * 70)

        # Display providers
        for provider in providers:
            status = "✓" if provider["available"] else "✗"
            reason = "" if provider["available"] else " (API key not set)"
            self.stdout.write(f"  {provider['id']}) {provider['name']:<25} {status}{reason}")

        self.stdout.write("-" * 70)
        self.stdout.write("")

        # Get provider selection
        selected_provider = None
        if options.get("provider"):
            # Try to match by name or key
            provider_input = options["provider"].lower()
            for provider in providers:
                if (
                    provider_input == provider["id"]
                    or provider_input == provider["key"]
                    or provider_input in provider["name"].lower()
                ):
                    selected_provider = provider
                    break
        else:
            # Interactive selection
            while True:
                try:
                    selection = input("Select provider (1-5) or name: ").strip()
                    if not selection:
                        continue

                    # Try to match selection
                    for provider in providers:
                        if (
                            selection == provider["id"]
                            or selection.lower() == provider["key"]
                            or selection.lower() in provider["name"].lower()
                        ):
                            selected_provider = provider
                            break

                    if selected_provider:
                        break
                    else:
                        self.stdout.write("Invalid selection. Please choose from available providers.")
                except (EOFError, KeyboardInterrupt):
                    self.stdout.write("\nExiting...")
                    return

        if not selected_provider:
            self.stdout.write("No provider selected. Exiting...")
            return

        # Check if provider is available
        if not selected_provider["available"]:
            self.stdout.write(f"⚠️  {selected_provider['name']} is not available (API key not set)")
            self.stdout.write("")
            self.stdout.write("To set the API key:")
            self.stdout.write("  1. Add it to your .env file or environment variables")
            self.stdout.write("  2. Or add it via Django Admin → Chat → AI Credentials")
            return

        # Start chat interface
        self.stdout.write(f"\n✓ Using {selected_provider['name']}")
        self.stdout.write("Type 'exit' or 'quit' to end the conversation.\n")

        try:
            self._start_chat(selected_provider)
        except KeyboardInterrupt:
            self.stdout.write("\n\nExiting...")
        except Exception as e:
            self.stdout.write(f"\nError: {e}")

    def _start_chat(self, provider):
        """Start interactive chat with the selected provider"""
        api_key = provider["api_key"]
        provider_key = provider["key"]

        if provider_key == "openai":
            self._chat_openai(api_key)
        elif provider_key == "anthropic":
            self._chat_anthropic(api_key)
        elif provider_key == "google":
            self._chat_google(api_key)
        elif provider_key == "xai":
            self._chat_xai(api_key)
        elif provider_key == "cursor":
            self._chat_cursor(api_key)
        else:
            self.stdout.write(f"Provider {provider_key} not yet implemented")

    def _chat_openai(self, api_key):
        """Chat with OpenAI"""
        try:
            from openai import OpenAI
        except ImportError:
            self.stdout.write("Error: openai package not installed. Run: pip install openai")
            return

        client = OpenAI(api_key=api_key)
        model = getattr(settings, "AI_CHAT_OPENAI_MODEL", "gpt-4o")

        messages = []
        while True:
            try:
                user_input = input("\nYou: ").strip()
                if not user_input:
                    continue
                if user_input.lower() in ["exit", "quit"]:
                    break

                messages.append({"role": "user", "content": user_input})
                response = client.chat.completions.create(
                    model=model,
                    messages=messages,
                )
                assistant_message = response.choices[0].message.content
                messages.append({"role": "assistant", "content": assistant_message})
                self.stdout.write(f"\nAssistant: {assistant_message}")

            except KeyboardInterrupt:
                break
            except Exception as e:
                self.stdout.write(f"\nError: {e}")

    def _chat_anthropic(self, api_key):
        """Chat with Anthropic Claude"""
        try:
            import anthropic
        except ImportError:
            self.stdout.write("Error: anthropic package not installed. Run: pip install anthropic")
            return

        client = anthropic.Anthropic(api_key=api_key)
        messages = []

        while True:
            try:
                user_input = input("\nYou: ").strip()
                if not user_input:
                    continue
                if user_input.lower() in ["exit", "quit"]:
                    break

                messages.append({"role": "user", "content": user_input})
                response = client.messages.create(
                    model="claude-3-5-sonnet-20241022",
                    max_tokens=1024,
                    messages=messages,
                )
                assistant_message = response.content[0].text
                messages.append({"role": "assistant", "content": assistant_message})
                self.stdout.write(f"\nAssistant: {assistant_message}")

            except KeyboardInterrupt:
                break
            except Exception as e:
                self.stdout.write(f"\nError: {e}")

    def _chat_google(self, api_key):
        """Chat with Google Gemini"""
        try:
            import google.generativeai as genai
        except ImportError:
            self.stdout.write("Error: google-generativeai package not installed. Run: pip install google-generativeai")
            return

        genai.configure(api_key=api_key)
        model = genai.GenerativeModel("gemini-pro")
        chat = model.start_chat(history=[])

        while True:
            try:
                user_input = input("\nYou: ").strip()
                if not user_input:
                    continue
                if user_input.lower() in ["exit", "quit"]:
                    break

                response = chat.send_message(user_input)
                self.stdout.write(f"\nAssistant: {response.text}")

            except KeyboardInterrupt:
                break
            except Exception as e:
                self.stdout.write(f"\nError: {e}")

    def _chat_xai(self, api_key):
        """Chat with xAI Grok"""
        self.stdout.write("xAI (Grok) integration not yet implemented")
        self.stdout.write("API key retrieved successfully, but chat interface needs implementation")

    def _chat_cursor(self, api_key):
        """Chat with Cursor IDE"""
        self.stdout.write("Cursor IDE integration not yet implemented")
        self.stdout.write("API key retrieved successfully, but chat interface needs implementation")
