from django.conf import settings
from openai import AsyncOpenAI, OpenAI

_client = None
_async_client = None


def get_openai_client():
    global _client
    if _client is None:
        _client = OpenAI(api_key=settings.AI_CHAT_OPENAI_API_KEY)
    return _client


def get_openai_async_client():
    # only instantiate client once, for performance reasons: https://github.com/openai/openai-python/issues/874
    global _async_client
    if _async_client is None:
        _async_client = AsyncOpenAI(api_key=settings.AI_CHAT_OPENAI_API_KEY)
    return _async_client
