from django.urls import path

from .views import MobileSnapshotStatusView, MobileSnapshotView

app_name = "mobile_sync"

urlpatterns = [
    path("snapshot/", MobileSnapshotView.as_view(), name="snapshot"),
    path("snapshot/<str:scope>/", MobileSnapshotStatusView.as_view(), name="snapshot-status"),
]
