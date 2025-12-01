# Generated manually to fix djstripe migration issue
# This migration handles the case where tax_percent column doesn't exist
# when djstripe.0008_2_5 tries to remove it.
#
# IMPORTANT: After this migration runs, you may need to fake the RemoveField
# operation in djstripe.0008_2_5 if the column doesn't exist. See the
# reverse function for instructions.

from django.db import migrations, connection


def remove_tax_percent_safely(apps, schema_editor):
    """
    Safely remove tax_percent column if it exists.
    This runs before djstripe.0008_2_5 to prevent migration errors.
    """
    with connection.cursor() as cursor:
        # Check if column exists and remove it if it does
        cursor.execute("""
            DO $$ 
            BEGIN 
                IF EXISTS (
                    SELECT 1 
                    FROM information_schema.columns 
                    WHERE table_schema = 'public'
                    AND table_name = 'djstripe_subscription' 
                    AND column_name = 'tax_percent'
                ) THEN
                    ALTER TABLE djstripe_subscription DROP COLUMN tax_percent;
                END IF;
            END $$;
        """)


def reverse_remove_tax_percent(apps, schema_editor):
    """
    Reverse operation. Note: We can't reliably recreate the column
    as we don't know its original definition.
    """
    # No-op: can't reverse a column removal without knowing the original definition
    pass


class Migration(migrations.Migration):
    # This migration must run before djstripe.0008_2_5
    # We depend on 0001_initial (same as 0008_2_5) but since 'web' 
    # comes after 'djstripe' alphabetically, we need to ensure proper ordering
    dependencies = [
        ("web", "0002_patch_djstripe_column"),
        ("djstripe", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(
            remove_tax_percent_safely,
            reverse_remove_tax_percent,
        ),
    ]

