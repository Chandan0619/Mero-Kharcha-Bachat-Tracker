from django.test import TestCase, Client
from django.contrib.auth.models import User
from finance.models import Income, Expense
from django.urls import reverse
from datetime import date
from django.utils import timezone

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
        self.assertEqual(response.context['savings'], 500)
        print("Dashboard Calcs: OK")

    def test_download_report_pdf(self):
        # Create some data
        Expense.objects.create(user=self.user, category='TestCat', amount=100, date=date.today())
        
        response = self.client.get(reverse('download_report_pdf'))
        
        # If xhtml2pdf is not installed/working, it might return 500 or just fail. 
        # But assuming it works or we want to verify it tries to work.
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/pdf')
        print("PDF Download: OK")

    def test_send_reminders_command(self):
        from django.core.management import call_command
        from django.core import mail
        from finance.models import Reminder
        from datetime import timedelta
        
        # Create a user with email
        self.user.email = 'test@example.com'
        self.user.save()
        
        # Create a due reminder
        due_reminder = Reminder.objects.create(
            user=self.user,
            title='Test Reminder',
            message='Test Message',
            reminder_date=timezone.now() - timedelta(minutes=10), # Past
            is_completed=False,
            email_sent=False
        )
        
        # Run command
        call_command('send_reminders')
        
        # Verify email sent
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].subject, 'Reminder: Test Reminder')
        
        # Verify flag update
        due_reminder.refresh_from_db()
        self.assertTrue(due_reminder.email_sent)
        print("Email Reminder: OK")

    def test_add_budget_new_category(self):
        from finance.models import Budget, ExpenseCategory
        response = self.client.post(reverse('add_budget'), {
            'category': 'Add New',
            'new_category': 'Vacation',
            'limit_amount': 20000,
            'period': 'Monthly',
            'start_date': date.today()
        })
        self.assertEqual(response.status_code, 302) # Redirects to dashboard
        
        # Check Budget created using new category
        self.assertTrue(Budget.objects.filter(user=self.user, category='Vacation').exists())
        
        # Check Category saved
        self.assertTrue(ExpenseCategory.objects.filter(user=self.user, name='Vacation').exists())
        print("Budget with New Category: OK")
