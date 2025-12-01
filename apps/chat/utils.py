from django.conf import settings
from openai import AsyncOpenAI, OpenAI, APIError, AuthenticationError

_client = None
_async_client = None


def validate_api_key():
    """Validate that the OpenAI API key is set and valid"""
    api_key = settings.AI_CHAT_OPENAI_API_KEY
    if not api_key:
        raise ValueError(
            "AI_CHAT_OPENAI_API_KEY is not set. Please set it in your environment variables or .env file."
        )
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
