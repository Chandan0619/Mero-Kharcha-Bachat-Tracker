from django.contrib import admin
from .models import Income, Expense, SavingsGoal, Budget, Reminder, Savings

# Register your models here.
admin.site.register(Income)
admin.site.register(Expense)
admin.site.register(SavingsGoal)
admin.site.register(Budget)
admin.site.register(Reminder)
admin.site.register(Savings)
