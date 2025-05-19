import logging
from django.db import transaction


from .models import (
    CV,
    SYNC_STATUS_COMPLETED,
    Achievement,
    Education,
    Language,
    Skill,
    WorkExperience,
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def clean_null_bytes(text):
    if text is None:
        return None
    return text.replace("\x00", "")


def delete_cv_and_related(document):
    """Delete CV and all related records within a transaction."""
    with transaction.atomic():
        Skill.objects.filter(cv=document).delete()
        Education.objects.filter(cv=document).delete()
        WorkExperience.objects.filter(cv=document).delete()
        Achievement.objects.filter(cv=document).delete()
        Language.objects.filter(cv=document).delete()
        CV.objects.filter(id=document.id).delete()
    logger.info(f"Deleted CV record with ID: {document.id}")


def extract_and_save_cv_data(document, cv_data):
    """Extract and save CV data to database."""
    with transaction.atomic():
        # Update CV record
        CV.objects.filter(id=document.id).update(
            raw_output=clean_null_bytes(cv_data.get("raw_output")),
            candidate_name=clean_null_bytes(cv_data.get("candidate_name")),
            candidate_email=clean_null_bytes(cv_data.get("candidate_email")),
            candidate_phone=clean_null_bytes(cv_data.get("candidate_phone")),
            candidate_title=clean_null_bytes(cv_data.get("candidate_title")),
            description=clean_null_bytes(cv_data.get("description")),
            overall_score=cv_data.get("overall_score"),
            experience_score=cv_data.get("experience_score"),
            achievement_score=cv_data.get("achievement_score"),
            skill_score=cv_data.get("skill_score"),
            sync_status=SYNC_STATUS_COMPLETED,
        )

        # Create related records
        for skill in cv_data.get("skills", []):
            Skill.objects.create(
                cv=document,
                skill=clean_null_bytes(skill.get("skill")),
                proficiency=clean_null_bytes(skill.get("proficiency")),
            )

        for education in cv_data.get("education", []):
            Education.objects.create(
                cv=document,
                degree=clean_null_bytes(education.get("degree")),
                year=clean_null_bytes(education.get("year")),
                institution=clean_null_bytes(education.get("institution")),
            )

        for work_experience in cv_data.get("workexperience", []):
            WorkExperience.objects.create(
                cv=document,
                position=clean_null_bytes(work_experience.get("position")),
                company=clean_null_bytes(work_experience.get("company")),
                duration=clean_null_bytes(work_experience.get("duration")),
                description=clean_null_bytes(work_experience.get("description")),
            )

        for achievement in cv_data.get("achievements", []):
            Achievement.objects.create(
                cv=document,
                title=clean_null_bytes(achievement.get("title")),
                description=clean_null_bytes(achievement.get("description")),
                year=clean_null_bytes(achievement.get("year")),
                publisher=clean_null_bytes(achievement.get("publisher")),
            )

        for language in cv_data.get("language", []):
            Language.objects.create(
                cv=document,
                language=clean_null_bytes(language.get("language")),
                proficiency=clean_null_bytes(language.get("proficiency")),
            )
