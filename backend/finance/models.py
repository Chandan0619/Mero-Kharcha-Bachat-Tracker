from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

class IncomeCategory(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=50)
    is_default = models.BooleanField(default=False)

    def __str__(self):
        return self.name

class ExpenseCategory(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=50)
    is_default = models.BooleanField(default=False)

    def __str__(self):
        return self.name

class PaymentMethod(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=50)
    is_default = models.BooleanField(default=False)

    def __str__(self):
        return self.name

class Income(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    source = models.CharField(max_length=50) # Removing choices to allow dynamic categories
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    date = models.DateTimeField(default=timezone.now)
    description = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.source} - {self.amount}"

class Expense(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    category = models.CharField(max_length=50) # Removing choices to allow dynamic categories
    payment_method = models.CharField(max_length=50, default='Cash')
    source_type = models.CharField(max_length=10, default='Income', choices=[('Income', 'Income'), ('Savings', 'Savings')])
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    date = models.DateTimeField(default=timezone.now)
    description = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.category} - {self.amount}"

class SavingsGoal(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=255)
    target_amount = models.DecimalField(max_digits=12, decimal_places=2)
    current_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    target_date = models.DateField()

    def __str__(self):
        return self.name

class Budget(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    category = models.CharField(max_length=50)
    limit_amount = models.DecimalField(max_digits=10, decimal_places=2)
    period = models.CharField(max_length=20, default='Monthly')
    start_date = models.DateField(default=timezone.now)
    end_date = models.DateField(blank=True, null=True)

    def __str__(self):
        return f"{self.category} Budget"

class Reminder(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    title = models.CharField(max_length=255)
    message = models.TextField(blank=True, null=True)
    reminder_date = models.DateTimeField()
    is_completed = models.BooleanField(default=False)
    email_sent = models.BooleanField(default=False)

    def __str__(self):
        return self.title

class Savings(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    income = models.ForeignKey(Income, on_delete=models.CASCADE, null=True, blank=True, related_name='autosavings')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    date = models.DateField(default=timezone.now)
    description = models.TextField(blank=True, null=True)
    is_automatic = models.BooleanField(default=False)

    def __str__(self):
        return f"Savings - {self.amount} ({'Auto' if self.is_automatic else 'Manual'})"
