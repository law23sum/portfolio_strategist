from django.test import SimpleTestCase
from djstripe.settings import djstripe_settings

from apps.users.models import CustomUser


class SubscriberModelTest(SimpleTestCase):
    def test_get_subscriber_model(self):
        model = djstripe_settings.get_subscriber_model()
        self.assertEqual(model, CustomUser)
