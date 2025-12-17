from django.conf import settings
from openai import APIError, AsyncOpenAI, AuthenticationError, OpenAI

_client = None
_async_client = None


def get_ai_api_key(provider: str) -> str | None:
    """
    Get API key for an AI provider from database or environment.

    Priority:
    1. Database (AICredential model) - if active credential exists
    2. Environment variable / Django settings

    Args:
        provider: One of 'openai', 'anthropic', 'google', 'xai', 'cursor'

    Returns:
        API key string if found, None otherwise
    """
    # First, try to get from database
    try:
        from .models import AICredential

        credential = AICredential.objects.filter(provider=provider, is_active=True).first()

        if credential and credential.api_key:
            return credential.api_key
    except Exception:
        # If database lookup fails (e.g., migrations not run), fall through to env
        pass

    # Fall back to environment variables / Django settings
    provider_settings_map = {
        "openai": "AI_CHAT_OPENAI_API_KEY",
        "anthropic": "ANTHROPIC_API_KEY",
        "google": "CURSOR_AI_GEMINI_API_KEY",
        "xai": "XAI_API_KEY",
        "cursor": "CURSOR_API_KEY",
    }

    setting_name = provider_settings_map.get(provider)
    if setting_name:
        return getattr(settings, setting_name, None) or None

    return None


def validate_api_key():
    """Validate that the OpenAI API key is set and valid"""
    api_key = settings.AI_CHAT_OPENAI_API_KEY
    if not api_key:
        raise ValueError("AI_CHAT_OPENAI_API_KEY is not set. Please set it in your environment variables or .env file.")
    return api_key


def get_openai_client():
    global _client
    if _client is None:
        api_key = validate_api_key()
        _client = OpenAI(api_key=api_key)
    return _client


def get_openai_async_client():
    # only instantiate client once, for performance reasons: https://github.com/openai/openai-python/issues/874
    global _async_client
    if _async_client is None:
        api_key = validate_api_key()
        _async_client = AsyncOpenAI(api_key=api_key)
    return _async_client


def test_openai_connection():
    """Test the OpenAI API connection with a simple request"""
    try:
        client = get_openai_client()
        response = client.chat.completions.create(
            model=settings.AI_CHAT_OPENAI_MODEL,
            messages=[{"role": "user", "content": "Say 'OK' if you can read this."}],
            max_tokens=10,
        )
        return True, response.choices[0].message.content.strip()
    except AuthenticationError as e:
        return False, f"Authentication failed: {str(e)}. Please check your API key."
    except APIError as e:
        return False, f"API error: {str(e)}"
    except ValueError as e:
        return False, str(e)
    except Exception as e:
        return False, f"Unexpected error: {str(e)}"
