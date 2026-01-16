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
]
