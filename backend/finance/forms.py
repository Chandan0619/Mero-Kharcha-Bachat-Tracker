from django import forms
from django.utils import timezone
from .models import Income, Expense, SavingsGoal, Budget, Reminder

class IncomeForm(forms.ModelForm):
    new_category = forms.CharField(
        required=False, 
        label="Or add a new category",
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Type new category name...'})
    )
    time = forms.TimeField(
        required=False,
        widget=forms.TimeInput(attrs={'type': 'time', 'class': 'form-control'})
    )

    class Meta:
        model = Income
        fields = ['source', 'amount', 'date', 'description']
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'source': forms.Select(attrs={'class': 'form-select'}),
            'amount': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Enter amount'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Optional description'}),
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        if user:
            from .models import IncomeCategory
            categories = IncomeCategory.objects.filter(user=user).values_list('name', 'name')
            self.fields['source'].widget.choices = [('', 'Select Category')] + list(categories) + [('Add New', 'Add New Category')]
        
        # Set initial time
        if not self.initial.get('time'):
            self.initial['time'] = timezone.now().time().strftime('%H:%M')

class ExpenseForm(forms.ModelForm):
    new_category = forms.CharField(
        required=False, 
        label="Or add a new category",
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Type new category name...'})
    )
    new_payment_method = forms.CharField(
        required=False,
        label="Or add a new payment method",
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Type new payment method...'})
    )
    time = forms.TimeField(
        required=False,
        widget=forms.TimeInput(attrs={'type': 'time', 'class': 'form-control'})
    )

    class Meta:
        model = Expense
        fields = ['amount', 'category', 'new_category', 'payment_method', 'new_payment_method', 'source_type', 'date', 'time', 'description']
        widgets = {
            'amount': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Enter amount'}),
            'category': forms.Select(attrs={'class': 'form-control', 'id': 'category-select'}),
            'new_category': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter new category', 'id': 'new-category-input', 'style': 'display: none;'}),
            'payment_method': forms.Select(attrs={'class': 'form-control', 'id': 'payment-method-select'}),
            'new_payment_method': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter new payment method', 'id': 'new-payment-method-input', 'style': 'display: none;'}),
            'source_type': forms.Select(attrs={'class': 'form-control'}),
            'date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'time': forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Description (optional)'}),
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        if user:
            from .models import ExpenseCategory, PaymentMethod
            
            # Categories
            categories = ExpenseCategory.objects.filter(user=user).values_list('name', 'name')
            self.fields['category'].widget.choices = [('', 'Select Category')] + list(categories) + [('Add New', 'Add New Category')]
            
            # Payment Methods
            p_methods = PaymentMethod.objects.filter(user=user).values_list('name', 'name')
            self.fields['payment_method'].widget.choices = [('', 'Select Payment Method')] + list(p_methods) + [('Add New', 'Add New Payment Method')]

        # Set initial time
        if not self.initial.get('time'):
            self.initial['time'] = timezone.now().time().strftime('%H:%M')

class SavingsGoalForm(forms.ModelForm):
    class Meta:
        model = SavingsGoal
        fields = ['name', 'target_amount', 'current_amount', 'target_date']
        widgets = {
            'target_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'target_amount': forms.NumberInput(attrs={'class': 'form-control'}),
            'current_amount': forms.NumberInput(attrs={'class': 'form-control'}),
        }

class BudgetForm(forms.ModelForm):
    new_category = forms.CharField(
        required=False, 
        label="Or add a new category",
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Type new category name...'})
    )

    class Meta:
        model = Budget
        fields = ['category', 'limit_amount', 'period', 'start_date']
        widgets = {
            'category': forms.Select(attrs={'class': 'form-select'}),
            'limit_amount': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Enter limit amount'}),
            'period': forms.Select(choices=[('Weekly', 'Weekly'), ('Monthly', 'Monthly')], attrs={'class': 'form-select'}),
            'start_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        if user:
            from .models import ExpenseCategory
            categories = ExpenseCategory.objects.filter(user=user).values_list('name', 'name')
            self.fields['category'].widget.choices = [('', 'Select Category')] + list(categories) + [('Add New', 'Add New Category')]

class ReminderForm(forms.ModelForm):
    date = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'})
    )
    time = forms.TimeField(
        required=False,
        widget=forms.TimeInput(attrs={'type': 'time', 'class': 'form-control'})
    )

    class Meta:
        model = Reminder
        fields = ['title', 'message', 'date', 'time']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'message': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Set initial time
        if not self.initial.get('time'):
            self.initial['time'] = timezone.now().time().strftime('%H:%M')
        if not self.initial.get('date'):
            self.initial['date'] = timezone.now().date().strftime('%Y-%m-%d')
