from django.urls import path
from . import views

app_name = 'solutions'

urlpatterns = [
    path('budgeting/', views.budgeting_view, name='budgeting'),
    path("charts/", views.ChartsView.as_view(), name = "charts"),
]