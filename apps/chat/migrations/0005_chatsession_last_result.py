# Generated by Django 5.2.1 on 2025-05-18 15:07

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("chat", "0004_remove_chat_last_result"),
    ]

    operations = [
        migrations.AddField(
            model_name="chatsession",
            name="last_result",
            field=models.TextField(blank=True, null=True),
        ),
    ]
