from celery import shared_task
from django.conf import settings

from apps.chat.models import Chat, ChatMessage, MessageTypes
from apps.chat.serializers import ChatMessageSerializer
from apps.chat.utils import get_openai_client


@shared_task(bind=True)
def get_chat_response(self, chat_id: int, message: str) -> str:
    chat = Chat.objects.get(id=chat_id)
    client = get_openai_client()
    response = client.chat.completions.create(model=settings.AI_CHAT_OPENAI_MODEL, messages=chat.get_openai_messages())

    message = ChatMessage.objects.create(
        chat_id=chat_id,
        message_type=MessageTypes.AI,
        content=response.choices[0].message.content.strip(),
    )
    return ChatMessageSerializer(message).data


@shared_task
def set_chat_name(chat_id: int, message: str):
    chat = Chat.objects.get(id=chat_id)
    if not message:
        return
    elif len(message) < 20:
        # for short messages, just use them as the chat name. the summary won't help
        chat.name = message
        chat.save()
    else:
        # set the name with openAI
        system_naming_prompt = """
    You are SummaryBot. When I give you an input, your job is to summarize the intent of that input.
    Provide only the summary of the input and nothing else.
    Summaries should be less than 100 characters long.
    """
        messages = [
            {"role": "system", "content": system_naming_prompt},
            {"role": "user", "content": f"Summarize the following text: '{message}'"},
        ]
        client = get_openai_client()
        response = client.chat.completions.create(model=settings.AI_CHAT_OPENAI_MODEL, messages=messages)
        chat.name = response.choices[0].message.content[:100].strip()
        chat.save()
