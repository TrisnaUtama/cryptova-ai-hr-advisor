from django.core.management import call_command
from huey import crontab
from huey.contrib.djhuey import periodic_task


@periodic_task(crontab(minute="*"))
def refresh_dashboard_views_task():
    call_command("refresh_dashboard_views")
