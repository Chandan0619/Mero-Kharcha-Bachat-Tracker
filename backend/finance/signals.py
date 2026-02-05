from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from .models import Income, Savings
from decimal import Decimal

@receiver(post_save, sender=Income)
def create_or_update_auto_savings(sender, instance, created, **kwargs):
    # Calculate 20% savings
    savings_amount = instance.amount * Decimal('0.20')
    
    # Update or Create Savings record linked to this income
    savings, created = Savings.objects.update_or_create(
        income=instance,
        defaults={
            'user': instance.user,
            'amount': savings_amount,
            'date': instance.date.date() if hasattr(instance.date, 'date') else instance.date,
            'description': f"20% auto-savings from {instance.source}",
            'is_automatic': True
        }
    )

@receiver(post_delete, sender=Income)
def delete_auto_savings(sender, instance, **kwargs):
    # Delete the linked savings record when income is deleted
    Savings.objects.filter(income=instance, is_automatic=True).delete()
