from django.urls import path

from . import views
from . import api_views

app_name = "users"
urlpatterns = [
    path("profile/", views.profile, name="user_profile"),
    path("profile/api/", api_views.user_profile_api, name="user_profile_api"),
    path("profile/upload-image/", views.upload_profile_image, name="upload_profile_image"),
    path("api-keys/create/", views.create_api_key, name="create_api_key"),
    path("api-keys/revoke/", views.revoke_api_key, name="revoke_api_key"),
]
