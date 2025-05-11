import os
from django.db import models
from core.models import BaseModel
from django.contrib.auth.models import User

SYNC_STATUS_PENDING = "pending"
SYNC_STATUS_PROCESSING = "processing"
SYNC_STATUS_COMPLETED = "completed"

SYNC_STATUS_CHOICES = (
    (SYNC_STATUS_PENDING, "Pending"),
    (SYNC_STATUS_PROCESSING, "Processing"),
    (SYNC_STATUS_COMPLETED, "Completed"),
)

def uplaod_to(instance, filename):
    return os.path.join('cv', str(instance.user.id), filename)

# Create your models here.
class CV(BaseModel):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='cvs')
    file = models.FileField(upload_to=uplaod_to)
    file_name = models.CharField(max_length=255)
    raw_output = models.TextField(blank=True, null=True)
    candidate_name = models.CharField(max_length=255, null=True, blank=True)
    candidate_email = models.EmailField(null=True, blank=True)
    candidate_phone = models.CharField(max_length=50, null=True, blank=True)
    candidate_title = models.CharField(max_length=255, null=True, blank=True)
    description = models.TextField(blank=True, null=True)
    overall_score = models.FloatField(blank=True, null=True)
    experience_score = models.FloatField(blank=True, null=True)
    achievement_score = models.FloatField(blank=True, null=True)
    skill_score = models.FloatField(blank=True, null=True)
    sync_status = models.CharField(max_length=20, choices=SYNC_STATUS_CHOICES, default=SYNC_STATUS_PENDING)

    class Meta:
        db_table = 'cvs'
        ordering = ['-created_at']

class Skill(BaseModel):
    cv = models.ForeignKey(CV, on_delete=models.CASCADE, related_name='skills')
    skill = models.CharField(max_length=100, null=True, blank=True)
    proficiency = models.CharField(max_length=100, null=True, blank=True)

    class Meta:
        db_table = 'skills'
        ordering = ['-created_at']

class Language(BaseModel):
    cv = models.ForeignKey(CV, on_delete=models.CASCADE, related_name='languages')
    language = models.CharField(max_length=100, null=True, blank=True)
    proficiency = models.CharField(max_length=100, null=True, blank=True)  

    class Meta:
        db_table = 'languages'
        ordering = ['-created_at']

class Education(BaseModel):
    cv = models.ForeignKey(CV, on_delete=models.CASCADE, related_name='educations')
    degree = models.CharField(max_length=100, null=True, blank=True)
    year = models.CharField(max_length=20, null=True, blank=True)
    institution = models.CharField(max_length=255, null=True, blank=True)
    gpa = models.CharField(max_length=20, null=True, blank=True)   

    class Meta:
        db_table = 'educations'
        ordering = ['-created_at']

class WorkExperience(BaseModel):
    cv = models.ForeignKey(CV, on_delete=models.CASCADE, related_name='work_experiences')
    position = models.CharField(max_length=100, null=True, blank=True)
    company = models.CharField(max_length=255, null=True, blank=True)
    duration = models.CharField(max_length=100, null=True, blank=True)
    description = models.TextField(blank=True, null=True)

    class Meta:
        db_table = 'work_experiences'
        ordering = ['-created_at']

class Achievement(BaseModel):
    cv = models.ForeignKey(CV, on_delete=models.CASCADE, related_name='achievements')
    title = models.CharField(max_length=255, null=True, blank=True)
    description = models.TextField(blank=True, null=True)
    year = models.CharField(max_length=20, null=True, blank=True)
    publisher = models.CharField(max_length=255, null=True, blank=True)

    class Meta:
        db_table = 'achievements'
        ordering = ['-created_at']

