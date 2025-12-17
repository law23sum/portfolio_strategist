from django.urls import path

from . import views

app_name = "solutions"

urlpatterns = [
    path("budgeting/", views.budgeting_view, name="budgeting"),
    path("charts/", views.ChartsView.as_view(), name="charts"),
    path("tax-optimization/", views.tax_optimization_view, name="tax_optimization"),
    path("credit-improvement/", views.credit_improvement_view, name="credit_improvement"),
]
