from django.urls import path
from . import views

app_name = 'solutions'

urlpatterns = [
    path('budgeting/', views.budgeting_view, name='budgeting'),
]