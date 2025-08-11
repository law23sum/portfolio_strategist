from django.urls import path
from . import views

app_name = 'categories'

urlpatterns = [
    path('personal-sensitive/', views.personal_sensitive_view, name='personal_sensitive'),
]