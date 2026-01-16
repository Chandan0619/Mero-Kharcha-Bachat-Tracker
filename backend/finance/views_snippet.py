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
