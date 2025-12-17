from django.conf import settings
from django.core.management.base import BaseCommand

from apps.records.models import AggregationProvider


class Command(BaseCommand):
    help = "Bootstraps Plaid aggregation provider from settings"

    def handle(self, **options):
        plaid_client_id = getattr(settings, "PLAID_CLIENT_ID", "")
        plaid_secret = getattr(settings, "PLAID_SECRET", "")
        plaid_environment = getattr(settings, "PLAID_ENVIRONMENT", "sandbox")
        plaid_webhook_url = getattr(settings, "PLAID_WEBHOOK_URL", "")

        if not plaid_client_id or not plaid_secret:
            self.stdout.write(
                self.style.ERROR(
                    "\n======== ERROR ==========\n"
                    "PLAID_CLIENT_ID and PLAID_SECRET must be set in your settings.\n"
                    "Please add them to your .env file:\n"
                    "PLAID_CLIENT_ID=your_client_id\n"
                    "PLAID_SECRET=your_secret\n"
                    "PLAID_ENVIRONMENT=sandbox  # or 'development' or 'production'\n"
                )
            )
            return

        provider, created = AggregationProvider.objects.get_or_create(
            name="plaid",
            defaults={
                "display_name": "Plaid",
                "is_active": True,
                "api_key": plaid_client_id,
                "api_secret": plaid_secret,
                "environment": plaid_environment,
                "webhook_url": plaid_webhook_url,
            },
        )

        if not created:
            # Update existing provider
            provider.api_key = plaid_client_id
            provider.api_secret = plaid_secret
            provider.environment = plaid_environment
            provider.webhook_url = plaid_webhook_url
            provider.is_active = True
            provider.save()
            self.stdout.write(self.style.SUCCESS(f"Updated existing Plaid provider (environment: {plaid_environment})"))
        else:
            self.stdout.write(self.style.SUCCESS(f"Created Plaid provider (environment: {plaid_environment})"))

        # Test the connection
        try:
            from apps.records.aggregation_service import PlaidAggregationService

            PlaidAggregationService(provider)  # Verify service can be initialized
            self.stdout.write(self.style.SUCCESS("✓ Plaid service initialized successfully"))
        except Exception as e:
            self.stdout.write(self.style.WARNING(f"⚠ Could not initialize Plaid service: {e}"))
            self.stdout.write(
                self.style.WARNING("This might be due to invalid credentials or missing plaid-python package.")
            )
