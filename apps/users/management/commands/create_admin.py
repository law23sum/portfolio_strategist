"""
Management command to create an admin/superuser account.

Usage:
    python manage.py create_admin
    python manage.py create_admin --email admin@example.com --username admin
    python manage.py create_admin --email admin@example.com --username admin --password mypassword
"""

import getpass
import secrets
import string

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from apps.users.models import CustomUser


class Command(BaseCommand):
    help = "Create an admin/superuser account"

    def add_arguments(self, parser):
        parser.add_argument(
            "--email",
            type=str,
            help="Email address for the admin account",
            default="admin@example.com",
        )
        parser.add_argument(
            "--username",
            type=str,
            help="Username for the admin account",
        )
        parser.add_argument(
            "--password",
            type=str,
            help="Password for the admin account (if not provided, will be generated or prompted)",
        )
        parser.add_argument(
            "--first-name",
            type=str,
            dest="first_name",
            help="First name for the admin account",
            default="Admin",
        )
        parser.add_argument(
            "--last-name",
            type=str,
            dest="last_name",
            help="Last name for the admin account",
            default="User",
        )
        parser.add_argument(
            "--no-input",
            action="store_true",
            help="Generate password automatically without prompting",
        )
        parser.add_argument(
            "--force",
            action="store_true",
            help="Overwrite existing user if they exist",
        )

    def generate_password(self, length=16):
        """Generate a secure random password."""
        alphabet = string.ascii_letters + string.digits + "!@#$%^&*"
        password = "".join(secrets.choice(alphabet) for _ in range(length))
        return password

    def handle(self, *args, **options):
        email = options.get("email", "").strip()
        username = options.get("username", "").strip()
        password = options.get("password")
        first_name = options.get("first_name", "Admin")
        last_name = options.get("last_name", "User")
        no_input = options.get("no_input", False)
        force = options.get("force", False)

        # Validate email
        if not email:
            raise CommandError("Email is required. Use --email to specify.")

        # Generate username from email if not provided
        if not username:
            username = email.split("@")[0]

        # Check if user already exists
        user_exists = False
        try:
            existing_user = CustomUser.objects.get(email=email)
            user_exists = True
            if not force:
                raise CommandError(f"User with email '{email}' already exists. Use --force to overwrite.")
            else:
                self.stdout.write(self.style.WARNING(f"User '{email}' already exists. Updating..."))
                user = existing_user
        except CustomUser.DoesNotExist:
            # Check if username is taken
            if CustomUser.objects.filter(username=username).exists():
                if not force:
                    raise CommandError(
                        f"Username '{username}' is already taken. Use --force to overwrite or choose a different username."
                    )
                else:
                    existing_user = CustomUser.objects.get(username=username)
                    self.stdout.write(
                        self.style.WARNING(f"Username '{username}' is already taken. Updating existing user...")
                    )
                    user = existing_user
                    user_exists = True
            else:
                user = CustomUser()

        # Get or generate password
        if password:
            # Use provided password
            pass
        elif no_input:
            # Generate password automatically
            password = self.generate_password()
            self.stdout.write(self.style.SUCCESS(f"Generated password: {password}"))
        else:
            # Prompt for password
            password = getpass.getpass("Enter password (leave blank to generate): ")
            if not password:
                password = self.generate_password()
                self.stdout.write(self.style.SUCCESS(f"Generated password: {password}"))
            else:
                password_confirm = getpass.getpass("Confirm password: ")
                if password != password_confirm:
                    raise CommandError("Passwords do not match!")

        # Validate password
        if not password or len(password) < 8:
            raise CommandError("Password must be at least 8 characters long.")

        # Create or update user
        with transaction.atomic():
            user.email = email
            user.username = username
            user.first_name = first_name
            user.last_name = last_name
            user.is_superuser = True
            user.is_staff = True
            user.is_active = True
            user.set_password(password)
            user.save()

        # Display success message
        action = "Updated" if user_exists else "Created"
        self.stdout.write(
            self.style.SUCCESS(
                f"\n{action} admin account successfully!\n"
                f"  Email: {email}\n"
                f"  Username: {username}\n"
                f"  Name: {first_name} {last_name}\n"
                f"  Password: {'(hidden - use the password you provided)' if not no_input and password != self.generate_password() else password}\n"
                f"  Superuser: Yes\n"
                f"  Staff: Yes\n"
            )
        )

        self.stdout.write(
            self.style.WARNING(
                "\n⚠️  IMPORTANT: Save these credentials securely!\n"
                "You can now log in to the admin interface at /admin/"
            )
        )
