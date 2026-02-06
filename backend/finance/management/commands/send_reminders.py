from django.core.management.base import BaseCommand
from django.core.mail import send_mail
from django.utils import timezone
from finance.models import Reminder
from django.conf import settings

class Command(BaseCommand):
    help = 'Sends email reminders for reminders that are due and not yet sent'

    def handle(self, *args, **options):
        now = timezone.now()
        reminders = Reminder.objects.filter(
            reminder_date__lte=now,
            is_completed=False,
            email_sent=False
        )

        if not reminders.exists():
            self.stdout.write(self.style.SUCCESS("No pending reminders found."))
            return

        for reminder in reminders:
            try:
                subject = f"Reminder: {reminder.title}"
                message = f"Hi {reminder.user.username},\n\nThis is a reminder for: {reminder.title}\n\nMessage: {reminder.message}\nDate: {reminder.reminder_date}\n\nFrom Mero Kharcha Bachat Tracker."
                recipient_list = [reminder.user.email]
                
                if recipient_list and recipient_list[0]: # Validate email exists
                    send_mail(
                        subject,
                        message,
                        settings.EMAIL_HOST_USER, # From email
                        recipient_list,
                        fail_silently=False,
                    )
                    reminder.email_sent = True
                    reminder.save()
                    self.stdout.write(self.style.SUCCESS(f"Sent email for reminder: {reminder.title}"))
                else:
                     self.stdout.write(self.style.WARNING(f"User {reminder.user.username} has no email address. Skipping."))

            except Exception as e:
                self.stdout.write(self.style.ERROR(f"Failed to send email for {reminder.title}: {str(e)}"))
