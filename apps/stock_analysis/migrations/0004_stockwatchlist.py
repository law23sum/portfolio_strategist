from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("stock_analysis", "0003_marketdatacredential"),
    ]

    operations = [
        migrations.CreateModel(
            name="StockWatchSnapshot",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("symbol", models.CharField(max_length=12, unique=True)),
                ("current_price", models.DecimalField(blank=True, decimal_places=4, max_digits=14, null=True)),
                ("change_percent", models.DecimalField(blank=True, decimal_places=4, max_digits=7, null=True)),
                ("payload", models.JSONField(blank=True, default=dict)),
                ("news_items", models.JSONField(blank=True, default=list)),
                ("fetched_at", models.DateTimeField(blank=True, null=True)),
                ("last_error", models.TextField(blank=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={
                "ordering": ["symbol"],
            },
        ),
        migrations.CreateModel(
            name="StockWatchlistEntry",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("symbol", models.CharField(db_index=True, max_length=12)),
                ("nickname", models.CharField(blank=True, max_length=64)),
                ("notes", models.TextField(blank=True)),
                ("last_refreshed", models.DateTimeField(blank=True, null=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "snapshot",
                    models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="entries", to="stock_analysis.stockwatchsnapshot"),
                ),
                (
                    "user",
                    models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="stock_watchlist", to="users.customuser"),
                ),
            ],
            options={
                "ordering": ["symbol"],
                "unique_together": {("user", "symbol")},
            },
        ),
    ]
