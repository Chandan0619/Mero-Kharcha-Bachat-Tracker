from django.test import TestCase, Client
from django.contrib.auth.models import User
from finance.models import Income, Expense
from django.urls import reverse
from datetime import date

class FinanceTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='testuser', password='password')
        self.client.login(username='testuser', password='password')

    def test_dashboard_view(self):
        response = self.client.get(reverse('dashboard'))
        self.assertEqual(response.status_code, 200)
        print("Dashboard load: OK")

    def test_add_income(self):
        response = self.client.post(reverse('add_income'), {
            'source': 'Salary',
            'amount': 5000,
            'date': date.today(),
            'time': '10:00',
            'description': 'Monthly salary'
        })
        self.assertEqual(response.status_code, 302) # Redirects to dashboard
        self.assertTrue(Income.objects.filter(user=self.user, source='Salary').exists())
        print("Add Income: OK")

    def test_add_expense(self):
        response = self.client.post(reverse('add_expense'), {
            'category': 'Food',
            'payment_method': 'Cash',
            'amount': 100,
            'date': date.today(),
            'time': '12:00',
            'description': 'Groceries'
        })
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Expense.objects.filter(user=self.user, category='Food').exists())
        print("Add Expense: OK")

    def test_dashboard_data(self):
        # Create data
        Income.objects.create(user=self.user, source='Salary', amount=1000, date=date.today())
        Expense.objects.create(user=self.user, category='Rent', amount=500, date=date.today())
        
        response = self.client.get(reverse('dashboard'))
        self.assertEqual(response.context['income_total'], 1000)
        self.assertEqual(response.context['expense_total'], 500)
        self.assertEqual(response.context['savings'], 500)
        print("Dashboard Calcs: OK")
