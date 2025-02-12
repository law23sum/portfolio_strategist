from typing import Dict

from django.urls import reverse

CHAT_PLACEHOLDER = "__chat_id__"
TASK_PLACEHOLDER = "__task_id__"


def get_chat_api_url_templates() -> Dict[str, str]:
    def _get_chat_placeholder_url(url_name, extra_args=None):
        args = [999] + (extra_args or [])
        url = reverse(url_name, args=args)
        return url.replace("999", CHAT_PLACEHOLDER)

    return {
        "chat:api_new_chat_message": _get_chat_placeholder_url("chat:api_new_chat_message"),
        "chat:api_get_message_response": _get_chat_placeholder_url(
            "chat:api_get_message_response", extra_args=[TASK_PLACEHOLDER]
        ),
    }
