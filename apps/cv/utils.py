import logging
from django.db import transaction

from core.ai.chroma import chroma, openai_ef

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
    return text.replace("\x00", "").strip()


def delete_cv_from_sql_and_vector_db(
    document: CV, collection_name: str, only_sql: bool = False
):
    cv_id_str = str(document.id)
    logger.info(f"Initiating deletion for CV ID: {cv_id_str}.")

    if not only_sql:
        try:
            target_collection = chroma.get_collection(
                name=collection_name, embedding_function=openai_ef
            )
            target_collection.delete(where={"cv_id": cv_id_str})
            logger.info(
                f"Deleted chunks for CV ID {cv_id_str} from Chroma collection '{collection_name}'."
            )
        except Exception as e:
            logger.error(
                f"Error deleting chunks for CV ID {cv_id_str} from Chroma collection '{collection_name}': {e}. SQL deletion will proceed."
            )

    with transaction.atomic():
        Skill.objects.filter(cv_id=document.id).delete()
        Education.objects.filter(cv_id=document.id).delete()
        WorkExperience.objects.filter(cv_id=document.id).delete()
        Achievement.objects.filter(cv_id=document.id).delete()
        Language.objects.filter(cv_id=document.id).delete()
        CV.objects.filter(id=document.id).delete()
    logger.info(
        f"Deleted CV ID {cv_id_str} and its related records from the SQL database."
    )


def extract_and_save_cv_data(document: CV, cv_data_payload: dict, raw_content: str):
    """Extract and save CV data to database.
    `cv_data_payload` is expected to be a dictionary-like object (e.g. Pydantic model .dict() or .get() compatible).
    """
    with transaction.atomic():
        document.raw_output = clean_null_bytes(raw_content)
        document.candidate_name = clean_null_bytes(
            cv_data_payload.get("candidate_name")
        )
        document.candidate_email = clean_null_bytes(
            cv_data_payload.get("candidate_email")
        )
        document.candidate_phone = clean_null_bytes(
            cv_data_payload.get("candidate_phone")
        )
        document.candidate_title = clean_null_bytes(
            cv_data_payload.get("candidate_title")
        )
        document.description = clean_null_bytes(cv_data_payload.get("description"))
        document.candidate_category = clean_null_bytes(
            cv_data_payload.get("candidate_category")
        )

        document.overall_score = cv_data_payload.get("overall_score")
        document.experience_score = cv_data_payload.get("experience_score")
        document.achievement_score = cv_data_payload.get("achievement_score")
        document.skill_score = cv_data_payload.get("skill_score")

        document.sync_status = SYNC_STATUS_COMPLETED
        document.sync_error = None
        document.save()

        Skill.objects.filter(cv=document).delete()
        Education.objects.filter(cv=document).delete()
        WorkExperience.objects.filter(cv=document).delete()
        Achievement.objects.filter(cv=document).delete()
        Language.objects.filter(cv=document).delete()

        # Create related records
        for skill_item in cv_data_payload.get("skills", []):
            if skill_item and skill_item.get("skill"):
                Skill.objects.create(
                    cv=document,
                    skill=clean_null_bytes(skill_item.get("skill")),
                    proficiency=clean_null_bytes(skill_item.get("proficiency")),
                )

        for edu_item in cv_data_payload.get("education", []):
            if edu_item and edu_item.get("institution"):
                Education.objects.create(
                    cv=document,
                    degree=clean_null_bytes(edu_item.get("degree")),
                    year=clean_null_bytes(edu_item.get("year")),
                    institution=clean_null_bytes(edu_item.get("institution")),
                    gpa=clean_null_bytes(edu_item.get("gpa")),
                )

        for work_item in cv_data_payload.get("workexperience", []):
            if work_item and work_item.get("company"):
                WorkExperience.objects.create(
                    cv=document,
                    position=clean_null_bytes(work_item.get("position")),
                    company=clean_null_bytes(work_item.get("company")),
                    duration=clean_null_bytes(work_item.get("duration")),
                    description=clean_null_bytes(work_item.get("description")),
                )

        for ach_item in cv_data_payload.get("achievements", []):
            if ach_item and ach_item.get("title"):
                Achievement.objects.create(
                    cv=document,
                    title=clean_null_bytes(ach_item.get("title")),
                    description=clean_null_bytes(ach_item.get("description")),
                    year=clean_null_bytes(ach_item.get("year")),
                    publisher=clean_null_bytes(ach_item.get("publisher")),
                )

        for lang_item in cv_data_payload.get("language", []):
            if lang_item and lang_item.get("language"):
                Language.objects.create(
                    cv=document,
                    language=clean_null_bytes(lang_item.get("language")),
                    proficiency=clean_null_bytes(lang_item.get("proficiency")),
                )
    logger.info(
        f"Successfully extracted and saved data for CV ID: {document.id} to SQL database."
    )
