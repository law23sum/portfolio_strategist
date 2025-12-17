import typing

from django.http import HttpRequest
from rest_framework.permissions import BasePermission, IsAuthenticated
from rest_framework_api_key.permissions import BaseHasAPIKey

from .helpers import get_user_from_request
from .models import UserAPIKey


class HasUserAPIKey(BaseHasAPIKey):
    model = UserAPIKey

    def has_permission(self, request: HttpRequest, view: typing.Any) -> bool:
        has_perm = super().has_permission(request, view)
        if has_perm:
            # if they have permission, also populate the request.user object for convenience
            request.user = get_user_from_request(request)
        return has_perm


class IsAuthenticatedOrHasUserAPIKey(BasePermission):
    """
    Hybrid permission class that allows access if user is authenticated OR has a valid API key.
    This is more reliable than using the | operator which may not work correctly with DRF.
    """

    def has_permission(self, request: HttpRequest, view: typing.Any) -> bool:
        # Check if user is authenticated
        if IsAuthenticated().has_permission(request, view):
            return True

        # Check if user has a valid API key
        if HasUserAPIKey().has_permission(request, view):
            return True

        return False
