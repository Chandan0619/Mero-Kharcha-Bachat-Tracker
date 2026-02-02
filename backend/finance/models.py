from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

class Income(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    source = models.CharField(max_length=255)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    date = models.DateField(default=timezone.now)
    description = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.source} - {self.amount}"

class Expense(models.Model):
    CATEGORY_CHOICES = [
        ('Food', 'Food'),
        ('Rent', 'Rent'),
        ('Utilities', 'Utilities'),
        ('Transportation', 'Transportation'),
        ('Entertainment', 'Entertainment'),
        ('Health', 'Health'),
        ('Groceries', 'Groceries'),
        ('Other', 'Other'),
    ]
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    date = models.DateField(default=timezone.now)
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
    CATEGORY_CHOICES = Expense.CATEGORY_CHOICES
    
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES)
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

    def __str__(self):
        return self.title

class Savings(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    date = models.DateField(default=timezone.now)
    description = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"Savings - {self.amount}"
