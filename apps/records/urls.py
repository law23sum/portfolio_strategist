from django.urls import path

from . import views

app_name = "records"

urlpatterns = [
    path("", views.insights_view, name="insights"),
    path("insights/", views.insights_view, name="insights"),
    path("explorer/", views.explorer_view, name="explorer"),
    path("upload/", views.upload_view, name="upload"),
    path("documents/partial/", views.document_list_partial, name="document_list_partial"),
    path("delete/<int:pk>/", views.delete_document, name="delete_document"),
    path("details/<int:pk>/", views.personal_details, name="personal_details"),
]
