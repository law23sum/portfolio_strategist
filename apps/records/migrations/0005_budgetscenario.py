from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('records', '0004_bondassessment_cdassessment_savingsassessment_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='BudgetScenario',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=120)),
                ('inputs', models.JSONField(blank=True, default=dict)),
                ('results', models.JSONField(blank=True, default=dict)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='budget_scenarios', to='users.customuser')),
            ],
            options={
                'ordering': ['-updated_at', 'name'],
                'unique_together': {('user', 'name')},
            },
        ),
        migrations.AddIndex(
            model_name='budgetscenario',
            index=models.Index(fields=['user', '-updated_at'], name='records_bud_user_id_d6e2d8_idx'),
        ),
    ]
