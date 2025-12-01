"""
Management command to fix the djstripe migration issue with tax_percent column.

This command:
1. Checks if the tax_percent column exists in djstripe_subscription table
2. Removes it if it exists (so djstripe.0008_2_5 can proceed normally)
3. If it doesn't exist, provides instructions to fake the migration

Usage:
    docker compose exec web python manage.py fix_djstripe_tax_percent
"""

from django.core.management.base import BaseCommand
from django.db import connection


class Command(BaseCommand):
    help = "Fix djstripe migration issue with tax_percent column"

    def add_arguments(self, parser):
        parser.add_argument(
            '--fake-migration',
            action='store_true',
            help='Automatically fake the djstripe.0008_2_5 migration if column does not exist',
        )

    def handle(self, *args, **options):
        with connection.cursor() as cursor:
            # Check if column exists
            cursor.execute("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_schema = 'public'
                AND table_name = 'djstripe_subscription' 
                AND column_name = 'tax_percent'
            """)
            column_exists = cursor.fetchone() is not None

            if column_exists:
                self.stdout.write(
                    self.style.SUCCESS('Column "tax_percent" exists. Removing it...')
                )
                cursor.execute("ALTER TABLE djstripe_subscription DROP COLUMN tax_percent;")
                self.stdout.write(
                    self.style.SUCCESS(
                        'Column removed successfully. You can now run migrations normally:\n'
                        '  docker compose exec web python manage.py migrate'
                    )
                )
            else:
                self.stdout.write(
                    self.style.WARNING('Column "tax_percent" does not exist.')
                )
                self.stdout.write(
                    '\nThe migration djstripe.0008_2_5 will fail when trying to remove it.\n'
                )

                if options['fake_migration']:
                    self.stdout.write('Faking the djstripe.0008_2_5 migration...')
                    from django.core.management import call_command
                    try:
                        call_command('migrate', 'djstripe', '0008_2_5', '--fake')
                        self.stdout.write(
                            self.style.SUCCESS(
                                'Migration djstripe.0008_2_5 has been faked successfully.\n'
                                'You can now continue with migrations:\n'
                                '  docker compose exec web python manage.py migrate'
                            )
                        )
                    except Exception as e:
                        self.stdout.write(
                            self.style.ERROR(f'Error faking migration: {e}')
                        )
                else:
                    self.stdout.write(
                        'To fix this, run:\n'
                        '  docker compose exec web python manage.py fix_djstripe_tax_percent --fake-migration\n'
                        '\nOr manually fake the migration:\n'
                        '  docker compose exec web python manage.py migrate djstripe 0008_2_5 --fake'
                    )

