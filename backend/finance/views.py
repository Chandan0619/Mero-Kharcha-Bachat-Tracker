from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from django.db.models import Sum
from django.utils import timezone
from datetime import datetime
from .models import Income, Expense, SavingsGoal, Budget, Reminder, Savings
from .forms import IncomeForm, ExpenseForm, SavingsGoalForm, BudgetForm, ReminderForm
from .utils import render_to_pdf
from django.contrib.humanize.templatetags.humanize import intcomma

@login_required
def dashboard(request):
    # Overall statistics
    total_income = Income.objects.filter(user=request.user).aggregate(Sum('amount'))['amount__sum'] or 0
    total_expense = Expense.objects.filter(user=request.user).aggregate(Sum('amount'))['amount__sum'] or 0
    total_savings = total_income - total_expense
    total_automated_savings = Savings.objects.filter(user=request.user, is_automatic=True).aggregate(Sum('amount'))['amount__sum'] or 0
    unallocated_savings = total_savings - total_automated_savings

    today = timezone.localdate()
    yesterday = today - timezone.timedelta(days=1)
    last_30_days = today - timezone.timedelta(days=30)

    today_start = timezone.make_aware(datetime.combine(today, datetime.min.time()))
    today_end = timezone.make_aware(datetime.combine(today, datetime.max.time()))
    yesterday_start = timezone.make_aware(datetime.combine(yesterday, datetime.min.time()))
    yesterday_end = timezone.make_aware(datetime.combine(yesterday, datetime.max.time()))

    # Specific time period expenses
    today_expense = Expense.objects.filter(
        user=request.user, 
        date__range=(today_start, today_end)
    ).aggregate(Sum('amount'))['amount__sum'] or 0
    
    yesterday_expense = Expense.objects.filter(
        user=request.user, 
        date__range=(yesterday_start, yesterday_end)
    ).aggregate(Sum('amount'))['amount__sum'] or 0
    
    last_30_days_expense = Expense.objects.filter(
        user=request.user, 
        date__gte=timezone.make_aware(datetime.combine(last_30_days, datetime.min.time()))
    ).aggregate(Sum('amount'))['amount__sum'] or 0

    # Chart data: daily expenses and income for the last 7 days (including today)
    seven_days_ago = today - timezone.timedelta(days=6)
    
    # Construct aware start/end datetimes for the range to avoid SQLite date lookup issues
    start_dt = timezone.make_aware(timezone.datetime.combine(seven_days_ago, timezone.datetime.min.time()))
    end_dt = timezone.make_aware(timezone.datetime.combine(today, timezone.datetime.max.time()))

    # Fetch all relevant records using efficient range filter
    relevant_expenses = Expense.objects.filter(
        user=request.user, 
        date__gte=start_dt, 
        date__lte=end_dt
    )
    relevant_income = Income.objects.filter(
        user=request.user, 
        date__gte=start_dt, 
        date__lte=end_dt
    )
    
    # Aggregate in Python to avoid SQLite TruncDate issues
    expense_map = {}
    for exp in relevant_expenses:
        local_date = timezone.localtime(exp.date).date()
        expense_map[local_date] = expense_map.get(local_date, 0) + float(exp.amount)
        
    income_map = {}
    for inc in relevant_income:
        local_date = timezone.localtime(inc.date).date()
        income_map[local_date] = income_map.get(local_date, 0) + float(inc.amount)
    
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
    for tx in recent_transactions:
        tx.amount_f = intcomma(int(tx.amount))

    # Active Pockets (Budgets)
    active_budgets = Budget.objects.filter(user=request.user).order_by('end_date')
    
    weekly_pockets = []
    monthly_pockets = []
    
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
            remaining = (budget.limit_amount or 0) - spent
            
            pocket_data = {
                'category': budget.category,
                'limit': budget.limit_amount,
                'limit_f': intcomma(int(budget.limit_amount)),
                'spent': spent,
                'spent_f': intcomma(int(spent)),
                'remaining': remaining,
                'remaining_f': intcomma(int(remaining)),
                'period': budget.period,
                'end_date': budget.end_date,
                'start_date': budget.start_date
            }
            
            if budget.period == 'Weekly':
                weekly_pockets.append(pocket_data)
            else:
                monthly_pockets.append(pocket_data)

    context = {
        'income_total': total_income,
        'expense_total': total_expense,
        'savings': total_savings,
        'automated_savings': total_automated_savings,
        'unallocated_savings': unallocated_savings,
        
        # Formatted values for template display
        'income_total_f': intcomma(int(total_income)),
        'expense_total_f': intcomma(int(total_expense)),
        'savings_f': intcomma(int(total_savings)),
        'automated_savings_f': intcomma(int(total_automated_savings)),
        'unallocated_savings_f': intcomma(int(unallocated_savings)),
        'today_expense_f': intcomma(int(today_expense)),
        'last_30_days_expense_f': intcomma(int(last_30_days_expense)),
        
        'today_expense': today_expense,
        'yesterday_expense': yesterday_expense,
        'last_30_days_expense': last_30_days_expense,
        'chart_dates': chart_dates,
        'expense_chart_data': expense_chart_data,
        'income_chart_data': income_chart_data,
        'categories': categories,
        'recent_transactions': recent_transactions,
        'weekly_budgets': weekly_pockets,
        'monthly_budgets': monthly_pockets,
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
            
            # Create automatic savings (20%) - Now handled by signals
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
        form = BudgetForm(request.POST, user=request.user)
        if form.is_valid():
            budget = form.save(commit=False)
            budget.user = request.user
            
            # Handle Category
            category = form.cleaned_data.get('category')
            new_cat = form.cleaned_data.get('new_category')
            if category == 'Add New' and new_cat:
                from .models import ExpenseCategory
                ExpenseCategory.objects.get_or_create(user=request.user, name=new_cat)
                budget.category = new_cat
            else:
                budget.category = category

            # Calculate end_date based on period
            if budget.period == 'Weekly':
                budget.end_date = budget.start_date + timezone.timedelta(days=6)
            elif budget.period == 'Monthly':
                # Simple approximation: +30 days. Better would be relativedelta but let's stick to standard lib for now
                budget.end_date = budget.start_date + timezone.timedelta(days=30)
                
            budget.save()
            return redirect('dashboard')
    else:
        form = BudgetForm(user=request.user)
    
    weekly_budgets = Budget.objects.filter(user=request.user, period='Weekly').order_by('-start_date')
    monthly_budgets = Budget.objects.filter(user=request.user, period='Monthly').order_by('-start_date')
    
    for b in weekly_budgets:
        b.limit_f = intcomma(int(b.limit_amount))
    for b in monthly_budgets:
        b.limit_f = intcomma(int(b.limit_amount))
        
    context = {
        'form': form, 
        'title': 'Set Budget',
        'weekly_budgets': weekly_budgets,
        'monthly_budgets': monthly_budgets
    }
    return render(request, 'finance/add_budget.html', context)

@login_required
def delete_budget(request, pk):
    budget = get_object_or_404(Budget, pk=pk, user=request.user)
    budget.delete()
    return redirect('add_budget')

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
    return redirect(request.META.get('HTTP_REFERER', 'add_reminder'))

@login_required
def delete_reminder(request, pk):
    reminder = get_object_or_404(Reminder, pk=pk, user=request.user)
    reminder.delete()
    return redirect(request.META.get('HTTP_REFERER', 'add_reminder'))

@login_required
def finance_report(request):
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    
    expenses_query = Expense.objects.filter(user=request.user)
    income_query = Income.objects.filter(user=request.user)
    
    if start_date:
        try:
            sd = datetime.strptime(start_date, '%Y-%m-%d').date()
            start_dt = timezone.make_aware(timezone.datetime.combine(sd, timezone.datetime.min.time()))
            expenses_query = expenses_query.filter(date__gte=start_dt)
            income_query = income_query.filter(date__gte=start_dt)
        except ValueError:
            pass
            
    if end_date:
        try:
            ed = datetime.strptime(end_date, '%Y-%m-%d').date()
            end_dt = timezone.make_aware(timezone.datetime.combine(ed, timezone.datetime.max.time()))
            expenses_query = expenses_query.filter(date__lte=end_dt)
            income_query = income_query.filter(date__lte=end_dt)
        except ValueError:
            pass
        
    expenses_by_category = expenses_query.values('category').annotate(total=Sum('amount')).order_by('-total')
    income_total = income_query.aggregate(Sum('amount'))['amount__sum'] or 0
    expense_total = expenses_query.aggregate(Sum('amount'))['amount__sum'] or 0
    net_balance = income_total - expense_total
    
    # Fetch individual expenses for the detailed table
    expenses = expenses_query.order_by('-date')
    
    # Add formatted amounts to lists
    for item in expenses_by_category:
        item['total_f'] = intcomma(int(item['total']))
    
    for exp in expenses:
        exp.amount_f = intcomma(int(exp.amount))

    context = {
        'expenses_by_category': expenses_by_category,
        'expenses': expenses,
        'income_total': income_total,
        'expense_total': expense_total,
        'net_balance': net_balance,
        'income_total_f': intcomma(int(income_total)),
        'expense_total_f': intcomma(int(expense_total)),
        'net_balance_f': intcomma(int(net_balance)),
        'start_date': start_date,
        'end_date': end_date,
    }
    return render(request, 'finance/report.html', context)

@login_required
def download_report_pdf(request):
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    
    expenses_query = Expense.objects.filter(user=request.user)
    income_query = Income.objects.filter(user=request.user)
    
    if start_date:
        try:
            sd = datetime.strptime(start_date, '%Y-%m-%d').date()
            start_dt = timezone.make_aware(timezone.datetime.combine(sd, timezone.datetime.min.time()))
            expenses_query = expenses_query.filter(date__gte=start_dt)
            income_query = income_query.filter(date__gte=start_dt)
        except ValueError:
            pass
            
    if end_date:
        try:
            ed = datetime.strptime(end_date, '%Y-%m-%d').date()
            end_dt = timezone.make_aware(timezone.datetime.combine(ed, timezone.datetime.max.time()))
            expenses_query = expenses_query.filter(date__lte=end_dt)
            income_query = income_query.filter(date__lte=end_dt)
        except ValueError:
            pass
        
    expenses_by_category = expenses_query.values('category').annotate(total=Sum('amount')).order_by('-total')
    income_total = income_query.aggregate(Sum('amount'))['amount__sum'] or 0
    expense_total = expenses_query.aggregate(Sum('amount'))['amount__sum'] or 0
    net_balance = income_total - expense_total
    
    # Fetch individual expenses for the detailed table
    expenses = expenses_query.order_by('-date')
    
    context = {
        'expenses_by_category': expenses_by_category,
        'expenses': expenses,
        'income_total': income_total,
        'expense_total': expense_total,
        'net_balance': net_balance,
        'user': request.user,
        'start_date': start_date,
        'end_date': end_date,
    }
    pdf_response = render_to_pdf('finance/report_pdf.html', context)
    if pdf_response:
        filename = f"Financial_Report_{timezone.now().strftime('%Y-%m-%d')}.pdf"
        pdf_response['Content-Disposition'] = f'attachment; filename="{filename}"'
        return pdf_response
    return HttpResponse("Not found")

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
