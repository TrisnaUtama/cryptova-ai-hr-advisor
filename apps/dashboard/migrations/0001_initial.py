from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("chat", "0002_rename_answer_chat_message_remove_chat_question_and_more"),
    ]

    operations = [
        # 1. Total uploaded & processed cvs per day (with user_id)
        migrations.RunSQL(
            """
            CREATE MATERIALIZED VIEW IF NOT EXISTS cv_uploaded_per_day AS
            SELECT
                DATE(created_at) AS day,
                user_id,
                COUNT(*) AS total_uploaded
            FROM
                cvs
            GROUP BY
                DATE(created_at), user_id
            ORDER BY
                day DESC;
            """,
            reverse_sql="DROP MATERIALIZED VIEW IF EXISTS cv_uploaded_per_day;",
        ),
        migrations.RunSQL(
            """
            CREATE MATERIALIZED VIEW IF NOT EXISTS cv_processed_per_day AS
            SELECT
                DATE(created_at) AS day,
                user_id,
                COUNT(*) AS total_processed
            FROM
                cvs
            WHERE
                sync_status = 'completed'
            GROUP BY
                DATE(created_at), user_id
            ORDER BY
                day DESC;
            """,
            reverse_sql="DROP MATERIALIZED VIEW IF EXISTS cv_processed_per_day;",
        ),
        # 2. Total uploaded & processed cvs per week (with user_id)
        migrations.RunSQL(
            """
            CREATE MATERIALIZED VIEW IF NOT EXISTS cv_uploaded_per_week AS
            SELECT
                DATE_TRUNC('week', created_at)::date AS week,
                user_id,
                COUNT(*) AS total_uploaded
            FROM
                cvs
            GROUP BY
                week, user_id
            ORDER BY
                week DESC;
            """,
            reverse_sql="DROP MATERIALIZED VIEW IF EXISTS cv_uploaded_per_week;",
        ),
        migrations.RunSQL(
            """
            CREATE MATERIALIZED VIEW IF NOT EXISTS cv_processed_per_week AS
            SELECT
                DATE_TRUNC('week', created_at)::date AS week,
                user_id,
                COUNT(*) AS total_processed
            FROM
                cvs
            WHERE
                sync_status = 'completed'
            GROUP BY
                week, user_id
            ORDER BY
                week DESC;
            """,
            reverse_sql="DROP MATERIALIZED VIEW IF EXISTS cv_processed_per_week;",
        ),
        # 3. Average of cv score per week (with user_id)
        migrations.RunSQL(
            """
            CREATE MATERIALIZED VIEW IF NOT EXISTS cv_score_avg_per_week AS
            SELECT
                DATE_TRUNC('week', created_at)::date AS week,
                user_id,
                AVG(overall_score) AS avg_score
            FROM
                cvs
            WHERE
                sync_status = 'completed' AND overall_score IS NOT NULL
            GROUP BY
                week, user_id
            ORDER BY
                week DESC;
            """,
            reverse_sql="DROP MATERIALIZED VIEW IF EXISTS cv_score_avg_per_week;",
        ),
        # 4. Score distribution (not grouped by time, still add user_id)
        migrations.RunSQL(
            """
            CREATE MATERIALIZED VIEW IF NOT EXISTS cv_score_distribution AS
            SELECT
                user_id,
                width_bucket(overall_score, 0, 100, 5) AS score_bucket,
                COUNT(*) AS total
            FROM
                cvs
            WHERE
                sync_status = 'completed' AND overall_score IS NOT NULL
            GROUP BY
                user_id, score_bucket
            ORDER BY
                score_bucket;
            """,
            reverse_sql="DROP MATERIALIZED VIEW IF EXISTS cv_score_distribution;",
        ),
    ]
