from django.apps import AppConfig


class StockAnalysisConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.stock_analysis"
    label = "stock_analysis"
    verbose_name = "Stock Analysis"
    
    def ready(self):
        """Set up periodic Celery tasks for automatic stock data refresh."""
        try:
            from django_celery_beat.models import PeriodicTask, IntervalSchedule
            from django.utils import timezone
            
            # Create or get interval schedule for hourly refresh
            schedule, created = IntervalSchedule.objects.get_or_create(
                every=1,
                period=IntervalSchedule.HOURS,
            )
            
            # Create or update periodic task for comprehensive stock refresh
            task_name = 'apps.stock_analysis.tasks.periodic_refresh_stock_data'
            periodic_task, created = PeriodicTask.objects.get_or_create(
                name='Refresh Stock Data via Yahoo Finance Scraping',
                defaults={
                    'task': task_name,
                    'interval': schedule,
                    'enabled': True,
                    'description': 'Automatically refresh stock data for all watchlist symbols using comprehensive Yahoo Finance web scraping',
                }
            )
            
            # Update if it already exists but might be disabled
            if not created and not periodic_task.enabled:
                periodic_task.enabled = True
                periodic_task.interval = schedule
                periodic_task.save()
                
        except Exception as e:
            # Fail silently if celery beat tables don't exist yet
            import logging
            logger = logging.getLogger(__name__)
            logger.debug(f"Could not set up periodic tasks: {e}")

