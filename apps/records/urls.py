from django.urls import path
from . import views

app_name = 'records'

urlpatterns = [
    path('upload/', views.upload_records_view, name='upload_records'),
]