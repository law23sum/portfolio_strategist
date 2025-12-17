"""
Dark Mode Support Utilities
Provides functions to manage dark mode preferences
"""

from .models import UserPreference


def get_user_preference(user):
    """Get or create user preference"""
    preference, created = UserPreference.objects.get_or_create(
        user=user, defaults={"dark_mode_enabled": False, "theme": "auto"}
    )
    return preference


def toggle_dark_mode(user):
    """Toggle dark mode for user"""
    preference = get_user_preference(user)
    preference.dark_mode_enabled = not preference.dark_mode_enabled
    preference.theme = "dark" if preference.dark_mode_enabled else "light"
    preference.save()
    return preference.dark_mode_enabled


def set_theme(user, theme):
    """Set theme for user (light, dark, or auto)"""
    preference = get_user_preference(user)
    preference.theme = theme
    preference.dark_mode_enabled = theme == "dark"
    preference.save()
    return preference
