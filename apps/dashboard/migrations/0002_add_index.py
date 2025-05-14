from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("dashboard", "0001_initial"),
    ]

    operations = [
        migrations.RunSQL(
            sql="CREATE UNIQUE INDEX IF NOT EXISTS idx_cv_uploaded_per_day_day ON cv_uploaded_per_day(day);",
            reverse_sql="DROP INDEX IF EXISTS idx_cv_uploaded_per_day_day;",
        ),
        migrations.RunSQL(
            sql="CREATE UNIQUE INDEX IF NOT EXISTS idx_cv_processed_per_day_day ON cv_processed_per_day(day);",
            reverse_sql="DROP INDEX IF EXISTS idx_cv_processed_per_day_day;",
        ),
        migrations.RunSQL(
            sql="CREATE UNIQUE INDEX IF NOT EXISTS idx_cv_uploaded_per_week_week ON cv_uploaded_per_week(week);",
            reverse_sql="DROP INDEX IF EXISTS idx_cv_uploaded_per_week_week;",
        ),
        migrations.RunSQL(
            sql="CREATE UNIQUE INDEX IF NOT EXISTS idx_cv_processed_per_week_week ON cv_processed_per_week(week);",
            reverse_sql="DROP INDEX IF EXISTS idx_cv_processed_per_week_week;",
        ),
        migrations.RunSQL(
            sql="CREATE UNIQUE INDEX IF NOT EXISTS idx_cv_score_avg_per_week_week ON cv_score_avg_per_week(week);",
            reverse_sql="DROP INDEX IF EXISTS idx_cv_score_avg_per_week_week;",
        ),
        migrations.RunSQL(
            sql="CREATE UNIQUE INDEX IF NOT EXISTS idx_cv_score_distribution_score_bucket ON cv_score_distribution(score_bucket);",
            reverse_sql="DROP INDEX IF EXISTS idx_cv_score_distribution_score_bucket;",
        ),
    ]
