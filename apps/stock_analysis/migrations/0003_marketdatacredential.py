from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('stock_analysis', '0002_stockanalysis_benchmark_symbol_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='MarketDataCredential',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('provider', models.CharField(choices=[('polygon', 'Polygon.io'), ('alpha_vantage', 'Alpha Vantage')], max_length=50, unique=True)),
                ('label', models.CharField(blank=True, help_text='Optional note to help identify this key', max_length=128)),
                ('api_key', models.CharField(max_length=512)),
                ('is_active', models.BooleanField(default=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'verbose_name': 'Market Data Credential',
                'verbose_name_plural': 'Market Data Credentials',
                'ordering': ['provider'],
            },
        ),
    ]
