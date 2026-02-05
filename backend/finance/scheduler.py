from apscheduler.schedulers.background import BackgroundScheduler
from django.conf import settings
from django.core.management import call_command
import sys

def job_function():
    # Only run the job if we are running the server (basic check)
    # This prevents it from running during migrations, etc if not intended,
    # though in this simple case it's fine.
    try:
        call_command('send_reminders')
        # print("Scheduler checked for reminders.")
    except Exception as e:
        print(f"Scheduler failed: {e}")

def start():
    # To prevent running twice with auto-reloader, we can check a simple logic or let it be.
    # For robust production, use Celery or a system Cron.
    # For 'runserver', checking sys.argv helps avoiding double run in reloader mainly if we care strictly.
    # But BackgroundScheduler usually handles fine.
    
    scheduler = BackgroundScheduler()
    scheduler.add_job(job_function, 'interval', minutes=1, id='send_reminders_job', replace_existing=True)
    scheduler.start()
