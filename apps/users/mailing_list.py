from django.conf import settings
from mailchimp3 import MailChimp
from mailchimp3.mailchimpclient import MailChimpError
from sentry_sdk import capture_exception


def get_mailchimp_client():
    if getattr(settings, "MAILCHIMP_API_KEY", None) and getattr(settings, "MAILCHIMP_LIST_ID", None):
        return MailChimp(mc_api=settings.MAILCHIMP_API_KEY)
    else:
        return None


def subscribe_to_mailing_list(email_address):
    client = get_mailchimp_client()
    if not client:
        return

    try:
        client.lists.members.create_or_update(
            settings.MAILCHIMP_LIST_ID,
            email_address,
            {
                "email_address": email_address,
                "status_if_new": "subscribed",
            },
        )
    except MailChimpError as e:
        # likely it's just that they were already subscribed so don't worry about it
        # but do log to sentry
        capture_exception(e)
