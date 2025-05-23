# Generated by Django 5.2.1 on 2025-05-17 11:22

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("cv", "0005_alter_achievement_year_alter_cv_candidate_phone_and_more"),
    ]

    operations = [
        migrations.AlterField(
            model_name="cv",
            name="sync_status",
            field=models.CharField(
                choices=[
                    ("pending", "Pending"),
                    ("processing", "Processing"),
                    ("completed", "Completed"),
                    ("failed", "Failed"),
                ],
                default="pending",
                max_length=20,
            ),
        ),
    ]
