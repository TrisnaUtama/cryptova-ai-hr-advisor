from django.contrib.auth.models import User
from django.db import models

from core.models import BaseModel
from apps.job.models import Job


class ChatSession(BaseModel):
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="chat_sessions"
    )
    job = models.ForeignKey(Job, on_delete=models.CASCADE, related_name="job", null=True, blank=True)
    title = models.CharField(max_length=255, null=True, blank=True)
    last_result = models.TextField(null=True, blank=True)

    class Meta:
        db_table = "chat_sessions"
        ordering = ["-created_at"]


class Chat(BaseModel):
    session = models.ForeignKey(
        ChatSession, on_delete=models.CASCADE, related_name="chats"
    )
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="chats")
    role = models.CharField(max_length=50, null=True, blank=True)
    message = models.TextField(null=True, blank=True)

    class Meta:
        db_table = "chats"
        ordering = ["-created_at"]
