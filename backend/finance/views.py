from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.db.models import Sum
from django.utils import timezone
from .models import Income, Expense, SavingsGoal, Budget, Reminder, Savings
from .forms import IncomeForm, ExpenseForm, SavingsGoalForm, BudgetForm, ReminderForm

@login_required
def dashboard(request):
    # Overall statistics
    total_income = Income.objects.filter(user=request.user).aggregate(Sum('amount'))['amount__sum'] or 0
    total_expense = Expense.objects.filter(user=request.user).aggregate(Sum('amount'))['amount__sum'] or 0
    total_savings = total_income - total_expense
    total_automated_savings = Savings.objects.filter(user=request.user).aggregate(Sum('amount'))['amount__sum'] or 0

    today = timezone.now().date()
    yesterday = today - timezone.timedelta(days=1)
    last_30_days = today - timezone.timedelta(days=30)

    # Specific time period expenses
    today_expense = Expense.objects.filter(user=request.user, date=today).aggregate(Sum('amount'))['amount__sum'] or 0
    yesterday_expense = Expense.objects.filter(user=request.user, date=yesterday).aggregate(Sum('amount'))['amount__sum'] or 0
    last_30_days_expense = Expense.objects.filter(user=request.user, date__gte=last_30_days).aggregate(Sum('amount'))['amount__sum'] or 0

    # Chart data: daily expenses for the last 7 days (including today)
    chart_dates = []
    chart_data = []
    
    # We can optimize this by fetching all expenses in the last 7 days and then processing in Python
    seven_days_ago = today - timezone.timedelta(days=6)
    daily_expenses = Expense.objects.filter(
        user=request.user, 
        date__gte=seven_days_ago, 
        date__lte=today
    ).values('date').annotate(total=Sum('amount')).order_by('date')
    
    # Create a mapping for quick lookup
    expense_map = {item['date']: float(item['total']) for item in daily_expenses}
    
    for i in range(6, -1, -1):
        day = today - timezone.timedelta(days=i)
        chart_dates.append(day.strftime('%b %d')) # Better date format
        chart_data.append(expense_map.get(day, 0.0))

    # Category summary
    categories = Expense.objects.filter(user=request.user).values('category').annotate(total=Sum('amount')).order_by('-total')

    # Active Pockets (Budgets)
    active_budgets = Budget.objects.filter(user=request.user).order_by('end_date')
    
    pockets = []
    for budget in active_budgets:
        # Check if active
        is_active = True
        if budget.start_date and budget.end_date:
            if not (budget.start_date <= today <= budget.end_date):
                is_active = False # Skip inactive for "Active Pockets" list

        if is_active:
            # Calculate spent in this pocket's period and category
            expenses_query = Expense.objects.filter(
                user=request.user, 
                category=budget.category
            )
            
            if budget.start_date:
                expenses_query = expenses_query.filter(date__gte=budget.start_date)
            if budget.end_date:
                expenses_query = expenses_query.filter(date__lte=budget.end_date)
                
            spent = expenses_query.aggregate(Sum('amount'))['amount__sum'] or 0
            remaining = budget.limit_amount - spent
            
            pockets.append({
                'category': budget.category,
                'limit': budget.limit_amount,
                'spent': spent,
                'remaining': remaining,
                'period': budget.period,
                'end_date': budget.end_date,
                'start_date': budget.start_date
            })

    context = {
        'income_total': total_income,
        'expense_total': total_expense,
        'savings': total_savings,
        'automated_savings': total_automated_savings,
        'today_expense': today_expense,
        'yesterday_expense': yesterday_expense,
        'last_30_days_expense': last_30_days_expense,
        'chart_dates': chart_dates,
        'chart_data': chart_data,
        'categories': categories,
        'recent_income': Income.objects.filter(user=request.user).order_by('-date')[:5],
        'recent_expenses': Expense.objects.filter(user=request.user).order_by('-date')[:5],
        'savings_goals': SavingsGoal.objects.filter(user=request.user),
        'budgets': pockets, # Pass processed pockets as 'budgets'
        'reminders': Reminder.objects.filter(user=request.user, is_completed=False),
    }
    return render(request, 'finance/dashboard.html', context)

@login_required
def add_income(request):
    if request.method == 'POST':
        form = IncomeForm(request.POST)
        if form.is_valid():
            income = form.save(commit=False)
            income.user = request.user
            income.save()
            
            # Create automatic savings (20%)
            savings_amount = income.amount * 20 / 100
            Savings.objects.create(
                user=request.user,
                amount=savings_amount,
                date=income.date,
                description=f"20% savings from {income.source}"
            )
            return redirect('dashboard')
    else:
        form = IncomeForm()
    return render(request, 'finance/form.html', {'form': form, 'title': 'Add Income'})

@login_required
def add_expense(request):
    if request.method == 'POST':
        form = ExpenseForm(request.POST)
        if form.is_valid():
            expense = form.save(commit=False)
            expense.user = request.user
            expense.save()
            return redirect('dashboard')
    else:
        form = ExpenseForm()
    return render(request, 'finance/form.html', {'form': form, 'title': 'Add Expense'})

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
            
            # Calculate end_date based on period
            if budget.period == 'Weekly':
                budget.end_date = budget.start_date + timezone.timedelta(days=6)
            elif budget.period == 'Monthly':
                # Simple approximation: +30 days. Better would be relativedelta but let's stick to standard lib for now
                budget.end_date = budget.start_date + timezone.timedelta(days=30)
                
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
            reminder.save()
            return redirect('dashboard')
    else:
        form = ReminderForm()
    return render(request, 'finance/form.html', {'form': form, 'title': 'Add Reminder'})

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
