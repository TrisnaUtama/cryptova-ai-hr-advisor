from django.db import models

# 1. Untuk Materialized View: cv_uploaded_per_day
class CvUploadedPerDay(models.Model):
    day = models.DateField(primary_key=True)
    total_uploaded = models.IntegerField()

    class Meta:
        managed = False
        db_table = 'cv_uploaded_per_day'

# 2. Untuk Materialized View: cv_processed_per_day
class CvProcessedPerDay(models.Model):
    day = models.DateField(primary_key=True)
    total_processed = models.IntegerField()

    class Meta:
        managed = False
        db_table = 'cv_processed_per_day'

# 3. Untuk Materialized View: cv_uploaded_per_week
class CvUploadedPerWeek(models.Model):
    week = models.DateField(primary_key=True)
    total_uploaded = models.IntegerField()

    class Meta:
        managed = False
        db_table = 'cv_uploaded_per_week'

# 4. Untuk Materialized View: cv_processed_per_week
class CvProcessedPerWeek(models.Model):
    week = models.DateField(primary_key=True)
    total_processed = models.IntegerField()

    class Meta:
        managed = False
        db_table = 'cv_processed_per_week'

# 5. Untuk Materialized View: cv_score_avg_per_week
class CvScoreAvgPerWeek(models.Model):
    week = models.DateField(primary_key=True)
    avg_score = models.FloatField()

    class Meta:
        managed = False
        db_table = 'cv_score_avg_per_week'

# 6. Untuk Materialized View: cv_score_distribution
class CvScoreDistribution(models.Model):
    score_bucket = models.IntegerField(primary_key=True)  # e.g. 1 for 0-20, 2 for 21-40, dst
    total = models.IntegerField()

    class Meta:
        managed = False
        db_table = 'cv_score_distribution'