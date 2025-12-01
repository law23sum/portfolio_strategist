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
        "chat:api_clear_chat": _get_chat_placeholder_url("chat:api_clear_chat"),
        "chat:api_user_data": reverse("chat:api_user_data"),
    }


def get_menu_urls() -> Dict[str, Dict[str, str]]:
    """Get all menu URLs for the top navigation dropdowns"""
    return {
        "solutions": {
            "budgeting": reverse("solutions:budgeting"),
            "debt_consolidation": reverse("subscriptions:subscription_demo"),
            "investment_savings": reverse("web:investment_savings"),
            "tax_optimization": reverse("solutions:tax_optimization"),
            "credit_improvement": reverse("solutions:credit_improvement"),
        },
        "records": {
            "insights": reverse("records:insights"),
            "explorer": reverse("records:explorer"),
            "upload": reverse("records:upload"),
            "link_account": reverse("records:link_account"),
            "personal_sensitive": reverse("records:personal_sensitive"),
        },
        "account": {
            "subscription": reverse("subscriptions:subscription_details"),
            "profile": reverse("users:user_profile"),
            "change_password": reverse("account_change_password"),
            "logout": reverse("account_logout"),
        },
    }
