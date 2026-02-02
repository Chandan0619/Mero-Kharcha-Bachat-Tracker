from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.db.models import Sum
from django.utils import timezone
from .models import Income, Expense, SavingsGoal, Budget, Reminder
from .forms import IncomeForm, ExpenseForm, SavingsGoalForm, BudgetForm, ReminderForm

@login_required
def dashboard(request):
    # Overall statistics
    total_income = Income.objects.filter(user=request.user).aggregate(Sum('amount'))['amount__sum'] or 0
    total_expense = Expense.objects.filter(user=request.user).aggregate(Sum('amount'))['amount__sum'] or 0
    total_savings = total_income - total_expense

    today = timezone.now().date()
    yesterday = today - timezone.timedelta(days=1)
    last_30_days = today - timezone.timedelta(days=30)

    # Specific time period expenses
    today_expense = Expense.objects.filter(user=request.user, date__date=today).aggregate(Sum('amount'))['amount__sum'] or 0
    yesterday_expense = Expense.objects.filter(user=request.user, date__date=yesterday).aggregate(Sum('amount'))['amount__sum'] or 0
    last_30_days_expense = Expense.objects.filter(user=request.user, date__date__gte=last_30_days).aggregate(Sum('amount'))['amount__sum'] or 0

    # Chart data: daily expenses and income for the last 7 days (including today)
    from django.db.models.functions import TruncDate
    
    seven_days_ago = today - timezone.timedelta(days=6)
    
    # Daily Expenses
    daily_expenses = Expense.objects.filter(
        user=request.user, 
        date__date__gte=seven_days_ago, 
        date__date__lte=today
    ).annotate(date_only=TruncDate('date')).values('date_only').annotate(total=Sum('amount')).order_by('date_only')
    
    # Daily Income
    daily_income_qs = Income.objects.filter(
        user=request.user, 
        date__date__gte=seven_days_ago, 
        date__date__lte=today
    ).annotate(date_only=TruncDate('date')).values('date_only').annotate(total=Sum('amount')).order_by('date_only')
    
    # Create mappings for quick lookup
    expense_map = {item['date_only']: float(item['total']) for item in daily_expenses}
    income_map = {item['date_only']: float(item['total']) for item in daily_income_qs}
    
    chart_dates = []
    expense_chart_data = []
    income_chart_data = []
    
    for i in range(6, -1, -1):
        day = today - timezone.timedelta(days=i)
        chart_dates.append(day.strftime('%b %d'))
        expense_chart_data.append(expense_map.get(day, 0.0))
        income_chart_data.append(income_map.get(day, 0.0))

    # Category summary
    categories = Expense.objects.filter(user=request.user).values('category').annotate(total=Sum('amount')).order_by('-total')

    # Combined Transaction History
    recent_income = Income.objects.filter(user=request.user).order_by('-date')[:10]
    recent_expenses = Expense.objects.filter(user=request.user).order_by('-date')[:10]
    
    recent_transactions = []
    for inc in recent_income:
        inc.transaction_type = 'Income'
        recent_transactions.append(inc)
    for exp in recent_expenses:
        exp.transaction_type = 'Expense'
        recent_transactions.append(exp)
        
    # Sort merged list by date descending and take top 5
    recent_transactions = sorted(recent_transactions, key=lambda x: x.date, reverse=True)[:5]

    context = {
        'income_total': total_income,
        'expense_total': total_expense,
        'savings': total_savings,
        'today_expense': today_expense,
        'yesterday_expense': yesterday_expense,
        'last_30_days_expense': last_30_days_expense,
        'chart_dates': chart_dates,
        'expense_chart_data': expense_chart_data,
        'income_chart_data': income_chart_data,
        'categories': categories,
        'recent_transactions': recent_transactions,
        'savings_goals': SavingsGoal.objects.filter(user=request.user),
        'budgets': Budget.objects.filter(user=request.user),
        'reminders': Reminder.objects.filter(user=request.user, is_completed=False).order_by('reminder_date'),
    }
    return render(request, 'finance/dashboard.html', context)

@login_required
def all_transactions(request):
    income_records = Income.objects.filter(user=request.user).order_by('-date')
    expense_records = Expense.objects.filter(user=request.user).order_by('-date')
    
    transactions = []
    for inc in income_records:
        inc.transaction_type = 'Income'
        transactions.append(inc)
    for exp in expense_records:
        exp.transaction_type = 'Expense'
        transactions.append(exp)
        
    # Sort all transactions by date descending
    transactions = sorted(transactions, key=lambda x: x.date, reverse=True)
    
    context = {
        'transactions': transactions,
    }
    return render(request, 'finance/all_transactions.html', context)

@login_required
def add_income(request):
    from .models import IncomeCategory
    # Ensure some default categories exist if the user has none
    defaults = ['Salary', 'Bonus', 'Allowance', 'Overtime', 'Investment', 'Other']
    if not IncomeCategory.objects.filter(user=request.user).exists():
        for cat in defaults:
            IncomeCategory.objects.get_or_create(user=request.user, name=cat, is_default=True)

    if request.method == 'POST':
        form = IncomeForm(request.POST, user=request.user)
        if form.is_valid():
            income = form.save(commit=False)
            income.user = request.user
            
            source = form.cleaned_data.get('source')
            new_cat = form.cleaned_data.get('new_category')
            
            if source == 'Add New' and new_cat:
                IncomeCategory.objects.get_or_create(user=request.user, name=new_cat)
                income.source = new_cat
            else:
                income.source = source
            
            # Combine Date and Time
            date_val = form.cleaned_data.get('date')
            time_val = form.cleaned_data.get('time')
            if date_val and time_val:
                from datetime import datetime
                income.date = datetime.combine(date_val, time_val)
                # Ensure it's timezone aware if USE_TZ is True
                if timezone.is_aware(timezone.now()):
                    income.date = timezone.make_aware(income.date)
                
            income.save()
            return redirect('dashboard')
    else:
        form = IncomeForm(user=request.user)
    return render(request, 'finance/add_income.html', {'form': form, 'title': 'Add Income'})

@login_required
def add_expense(request):
    from .models import ExpenseCategory, PaymentMethod
    # Ensure some default categories exist
    defaults = ['Food', 'Rent', 'Utilities', 'Transportation', 'Entertainment', 'Health', 'Groceries', 'Other']
    if not ExpenseCategory.objects.filter(user=request.user).exists():
        for cat in defaults:
            ExpenseCategory.objects.get_or_create(user=request.user, name=cat, is_default=True)
    
    # Ensure default payment methods exist
    p_defaults = ['Esewa', 'Khalti', 'Mobile Banking', 'Cash']
    if not PaymentMethod.objects.filter(user=request.user).exists():
        for pm in p_defaults:
            PaymentMethod.objects.get_or_create(user=request.user, name=pm, is_default=True)

    if request.method == 'POST':
        form = ExpenseForm(request.POST, user=request.user)
        if form.is_valid():
            expense = form.save(commit=False)
            expense.user = request.user
            
            # Handle Category
            category = form.cleaned_data.get('category')
            new_cat = form.cleaned_data.get('new_category')
            if category == 'Add New' and new_cat:
                ExpenseCategory.objects.get_or_create(user=request.user, name=new_cat)
                expense.category = new_cat
            else:
                expense.category = category
            
            # Handle Payment Method
            pm = form.cleaned_data.get('payment_method')
            new_pm = form.cleaned_data.get('new_payment_method')
            if pm == 'Add New' and new_pm:
                PaymentMethod.objects.get_or_create(user=request.user, name=new_pm)
                expense.payment_method = new_pm
            else:
                expense.payment_method = pm
            
            # Combine Date and Time
            date_val = form.cleaned_data.get('date')
            time_val = form.cleaned_data.get('time')
            if date_val and time_val:
                from datetime import datetime
                expense.date = datetime.combine(date_val, time_val)
                if timezone.is_aware(timezone.now()):
                    expense.date = timezone.make_aware(expense.date)
                
            expense.save()
            return redirect('dashboard')
    else:
        form = ExpenseForm(user=request.user)
    return render(request, 'finance/add_expense.html', {'form': form, 'title': 'Add Expense'})

@login_required
def add_savings(request):
    if request.method == 'POST':
        form = SavingsGoalForm(request.POST)
        if form.is_valid():
            goal = form.save(commit=False)
            goal.user = request.user
            goal.save()
            return redirect('dashboard')
    else:
        form = SavingsGoalForm()
    return render(request, 'finance/form.html', {'form': form, 'title': 'Add Savings Goal'})

@login_required
def add_budget(request):
    if request.method == 'POST':
        form = BudgetForm(request.POST)
        if form.is_valid():
            budget = form.save(commit=False)
            budget.user = request.user
            budget.save()
            return redirect('dashboard')
    else:
        form = BudgetForm()
    return render(request, 'finance/form.html', {'form': form, 'title': 'Set Budget'})

@login_required
def add_reminder(request):
    if request.method == 'POST':
        form = ReminderForm(request.POST)
        if form.is_valid():
            reminder = form.save(commit=False)
            reminder.user = request.user
            
            # Combine Date and Time
            date_val = form.cleaned_data.get('date')
            time_val = form.cleaned_data.get('time')
            if date_val and time_val:
                from datetime import datetime
                reminder.reminder_date = datetime.combine(date_val, time_val)
                if timezone.is_aware(timezone.now()):
                    reminder.reminder_date = timezone.make_aware(reminder.reminder_date)
            
            reminder.save()
            return redirect('add_reminder')
    else:
        form = ReminderForm()
    
    active_reminders = Reminder.objects.filter(user=request.user, is_completed=False).order_by('reminder_date')
    completed_reminders = Reminder.objects.filter(user=request.user, is_completed=True).order_by('-reminder_date')
    
    context = {
        'form': form,
        'active_reminders': active_reminders,
        'completed_reminders': completed_reminders,
        'title': 'Reminders'
    }
    return render(request, 'finance/reminder_list.html', context)

@login_required
def complete_reminder(request, pk):
    reminder = get_object_or_404(Reminder, pk=pk, user=request.user)
    reminder.is_completed = True
    reminder.save()
    return redirect(request.META.get('HTTP_REFERER', 'dashboard'))

@login_required
def finance_report(request):
    expenses_by_category = Expense.objects.filter(user=request.user).values('category').annotate(total=Sum('amount')).order_by('-total')
    income_total = Income.objects.filter(user=request.user).aggregate(Sum('amount'))['amount__sum'] or 0
    expense_total = Expense.objects.filter(user=request.user).aggregate(Sum('amount'))['amount__sum'] or 0
    
    context = {
        'expenses_by_category': expenses_by_category,
        'income_total': income_total,
        'expense_total': expense_total,
    }
    return render(request, 'finance/report.html', context)

@login_required
def delete_income(request, pk):
    income = get_object_or_404(Income, pk=pk, user=request.user)
    income.delete()
    return redirect('all_transactions')

@login_required
def delete_expense(request, pk):
    expense = get_object_or_404(Expense, pk=pk, user=request.user)
    expense.delete()
    return redirect('all_transactions')
