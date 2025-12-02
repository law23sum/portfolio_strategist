# Generated migration to set up periodic stock data refresh

from django.db import migrations


def create_periodic_stock_refresh_task(apps, schema_editor):
    """Create periodic task to refresh stock data every hour"""
    from django_celery_beat.models import MINUTES
    IntervalSchedule = apps.get_model("django_celery_beat", "IntervalSchedule")
    PeriodicTask = apps.get_model("django_celery_beat", "PeriodicTask")
    
    # Create or get hourly schedule (every 60 minutes)
    hourly_schedule, created = IntervalSchedule.objects.get_or_create(
        every=60,
        period=MINUTES,
    )
    
    # Create periodic task if it doesn't exist
    PeriodicTask.objects.get_or_create(
        name="refresh-stock-data-hourly",
        defaults={
            "task": "apps.stock_analysis.tasks.periodic_refresh_stock_data",
            "interval": hourly_schedule,
            "enabled": True,
            "description": "Periodically refresh stock data for all watchlist symbols using comprehensive Yahoo Finance scraping",
        }
    )


def delete_periodic_stock_refresh_task(apps, schema_editor):
    """Remove periodic stock refresh task"""
    PeriodicTask = apps.get_model("django_celery_beat", "PeriodicTask")
    PeriodicTask.objects.filter(name="refresh-stock-data-hourly").delete()


class Migration(migrations.Migration):

    dependencies = [
        ("stock_analysis", "0004_stockwatchlist"),
        ("django_celery_beat", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(
            create_periodic_stock_refresh_task,
            reverse_code=delete_periodic_stock_refresh_task
        )
    ]

