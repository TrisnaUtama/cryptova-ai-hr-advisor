from huey import crontab
from huey.contrib.djhuey import periodic_task

from django.core.management import call_command


@periodic_task(crontab(minute="*"))
def refresh_dashboard_views_task():
    call_command("refresh_dashboard_views")
