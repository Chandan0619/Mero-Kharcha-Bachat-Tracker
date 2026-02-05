from django.urls import path
from . import views

urlpatterns = [
    path('dashboard/', views.dashboard, name='dashboard'),
    path('add-income/', views.add_income, name='add_income'),
    path('add-expense/', views.add_expense, name='add_expense'),
    path('add-savings/', views.add_savings, name='add_savings'),
    path('add-budget/', views.add_budget, name='add_budget'),
    path('add-reminder/', views.add_reminder, name='add_reminder'),
    path('reports/', views.finance_report, name='finance_report'),
    path('download-report/', views.download_report_pdf, name='download_report_pdf'),
    path('complete-reminder/<int:pk>/', views.complete_reminder, name='complete_reminder'),
    path('transactions/', views.all_transactions, name='all_transactions'),
    path('delete-income/<int:pk>/', views.delete_income, name='delete_income'),
    path('delete-expense/<int:pk>/', views.delete_expense, name='delete_expense'),
]
