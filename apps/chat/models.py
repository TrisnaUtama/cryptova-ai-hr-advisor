from django.db import models
from core.models import BaseModel
from django.contrib.auth.models import User

# Create your models here.
class Chat(BaseModel):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='chats')
    role = models.CharField(max_length=50, null=True, blank=True)
    question = models.TextField(null=True, blank=True)
    answer = models.TextField(null=True, blank=True)

    class Meta:
        db_table = 'chats'
        ordering = ['-created_at']
