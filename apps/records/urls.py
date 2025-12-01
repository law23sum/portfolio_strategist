from django.urls import path

from . import views
from . import aggregation_views

app_name = "records"

urlpatterns = [
    path("", views.insights_view, name="insights"),
    path("insights/", views.insights_view, name="insights"),
    path("explorer/", views.explorer_view, name="explorer"),
    path("upload/", views.upload_view, name="upload"),
    path("documents/partial/", views.document_list_partial, name="document_list_partial"),
    path("delete/<int:pk>/", views.delete_document, name="delete_document"),
    path("details/<int:pk>/", views.personal_details, name="personal_details"),
    # Financial data aggregation routes
    path("link-account/", aggregation_views.link_account_view, name="link_account"),
    path("linked-accounts/", aggregation_views.linked_accounts_view, name="linked_accounts"),
    path("account/<int:account_id>/", aggregation_views.account_detail_view, name="account_detail"),
    path("api/create-link-token/", aggregation_views.create_link_token, name="create_link_token"),
    path("api/exchange-token/", aggregation_views.exchange_token, name="exchange_token"),
    path("api/sync-account/<int:account_id>/", aggregation_views.sync_account, name="sync_account"),
    path("api/disconnect-account/<int:account_id>/", aggregation_views.disconnect_account, name="disconnect_account"),
    path("webhooks/plaid/", aggregation_views.plaid_webhook, name="plaid_webhook"),
]
