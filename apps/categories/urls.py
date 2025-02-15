from django.urls import path
from . import views

app_name = 'categories'

urlpatterns = [
    path('government/', views.government_view, name='government'),
]