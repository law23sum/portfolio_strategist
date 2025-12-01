from django.urls import path
from . import views

app_name = 'stock_analysis'

urlpatterns = [
    path('', views.stock_analysis_home, name='home'),
    path('analyze/', views.analyze_stock, name='analyze'),
    path('results/<int:pk>/', views.analysis_results, name='results'),
    path('planner/<int:analysis_pk>/', views.investment_planner, name='planner'),
    path('download/<int:pk>/', views.download_pdf, name='download_pdf'),
    path('loan/', views.personal_loan_analysis, name='loan'),
    path('loan/results/<int:pk>/', views.loan_results, name='loan_results'),
    # API endpoint for investment prediction
    path('api/investment-forecast/', views.investment_forecast_api, name='investment_forecast_api'),
    # API endpoint for stock details (reports, charts, graphs)
    path('api/stock-details/', views.stock_details_api, name='stock_details_api'),
]

