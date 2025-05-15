from django.core.management.base import BaseCommand
from django.db import connection


class Command(BaseCommand):
    help = "Refresh all dashboard materialized views"

    def handle(self, *args, **options):
        views = [
            "cv_uploaded_per_day",
            "cv_processed_per_day",
            "cv_uploaded_per_week",
            "cv_processed_per_week",
            "cv_score_avg_per_week",
            "cv_score_distribution",
        ]
        with connection.cursor() as cursor:
            for view in views:
                cursor.execute(f"REFRESH MATERIALIZED VIEW CONCURRENTLY {view};")
                self.stdout.write(self.style.SUCCESS(f"{view} refreshed!"))
