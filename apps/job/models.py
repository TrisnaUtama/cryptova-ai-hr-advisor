from django.db import models
from core.models import BaseModel
from django.contrib.auth.models import User
from apps.cv.models import CV

JOB_STATUS_CREATED = 'created'
JOB_STATUS_PROCESS = 'process'
JOB_STATUS_CLOSED = 'open'


JOB_STATUS_CHOICES = [
    (JOB_STATUS_CREATED, 'Created'),
    (JOB_STATUS_PROCESS, 'Process'),
    (JOB_STATUS_CLOSED, 'Open'),
]

class JobCategory(BaseModel):
    name = models.CharField(max_length=255)
    description = models.TextField()

    class Meta:
        db_table = 'job_categories'

# Create your models here.
class Job(BaseModel):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    title = models.CharField(max_length=255)
    description = models.TextField()
    location = models.CharField(max_length=255)
    salary_min = models.FloatField()
    salary_max = models.FloatField()
    job_category = models.ForeignKey(JobCategory, on_delete=models.CASCADE)
    min_experience = models.CharField()
    min_education = models.CharField()
    company_name = models.CharField(max_length=255)
    company_description = models.TextField()
    status = models.CharField(max_length=255, choices=JOB_STATUS_CHOICES, default=JOB_STATUS_CREATED)

    class Meta:
        db_table = 'jobs'

class JobApplication(BaseModel):
    job = models.ForeignKey(Job, on_delete=models.CASCADE)
    cv = models.ForeignKey(CV, on_delete=models.CASCADE)
    matching_score = models.FloatField()
    reason = models.TextField()

    class Meta:
        db_table = 'job_applications'
