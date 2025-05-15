from huey.contrib.djhuey import task
import logging

from .models import CV, Skill, Education, WorkExperience, Achievement, Language, SYNC_STATUS_PROCESSING, SYNC_STATUS_COMPLETED, SYNC_STATUS_FAILED
from core.methods import send_notification

from core.ai.mistral import mistral
from core.ai.prompt_manager import PromptManager, CVBase

logging.basicConfig(level=logging.INFO)

def clean_null_bytes(text):
    if text is None:
        return None
    return text.replace('\x00', '')

@task()
def process_cv(document: CV):
    filename = document.file.name
    try:
        # Upload the CV to Mistral
        uploaded_pdf = mistral.files.upload(
            file={
                "file_name": filename,
                "content": open(f"media/{filename}", "rb"),
            },
            purpose="ocr",
        )
        CV.objects.filter(id=document.id).update(sync_status=SYNC_STATUS_PROCESSING)

        # Get the signed URL for the uploaded file
        signed_url = mistral.files.get_signed_url(file_id=uploaded_pdf.id)
        logging.info(f"Signed URL: {signed_url}")

        send_notification("notification", "CV uploaded successfully", filename)

        # Process the document with Mistral OCR
        ocr_response = mistral.ocr.process(
            model="mistral-ocr-latest",
            document={"type": "document_url", "document_url": signed_url.url},
            include_image_base64=True,
        )

        # Check if the OCR response is successful
        content = ""
        for page in ocr_response.dict().get("pages", []):
            content += page.get("markdown")

        logging.info(f"Extracted document content length: {len(content)} characters")
        send_notification("notification", "CV processed successfully", filename)

        # Parse the CV content using Structured Output
        pm = PromptManager()
        pm.add_message(
            "system",
            """You are a CV parser that extracts structured information from resumes. 
                Extract detailed information following this structure:
                - Basic info: name, email, phone, job title
                - Summary description
                - Education history: degree, year, institution, GPA
                - Work experience: position, company, duration, description
                - Skills: skill name, proficiency level
                - Languages: language name, proficiency level
                - Achievements: title, description, year, publisher
                
                For all scores, use a scale of 0 to 100 where:
                - overall_score: overall quality of the CV
                - experience_score: relevance and quality of work experience
                - achievement_score: notable achievements
                - skill_score: breadth and depth of skills
                
                Ensure all data matches the database schema requirements.
                """,
        )
        pm.add_message("user", f"Extract information from this CV: {content}")

        cv_data = pm.generate_structured(CVBase)
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
        
        logging.info(f"Extracted CV: {cv_data}")
        # update the skills, education, and work experience
        for skill in cv_data.get("skills"):
            Skill.objects.create(
                cv=document,
                skill=clean_null_bytes(skill.get("skill")),
                proficiency=clean_null_bytes(skill.get("proficiency")),
            )
            
        for education in cv_data.get("education"):
            Education.objects.create(
                cv=document,
                degree=clean_null_bytes(education.get("degree")),
                year=clean_null_bytes(education.get("year")),
                institution=clean_null_bytes(education.get("institution")),
            )
        for work_experience in cv_data.get("workexperience"):
            WorkExperience.objects.create(
                cv=document,
                position=clean_null_bytes(work_experience.get("position")),
                company=clean_null_bytes(work_experience.get("company")),
                duration=clean_null_bytes(work_experience.get("duration")),
                description=clean_null_bytes(work_experience.get("description")),
            )
        for achievement in cv_data.get("achievements"):
            Achievement.objects.create(
                cv=document,
                title=clean_null_bytes(achievement.get("title")),
                description=clean_null_bytes(achievement.get("description")),
                year=clean_null_bytes(achievement.get("year")),
                publisher=clean_null_bytes(achievement.get("publisher")),
            )
        for language in cv_data.get("language"):
            Language.objects.create(
                cv=document,
                language=clean_null_bytes(language.get("language")),
                proficiency=clean_null_bytes(language.get("proficiency")),
            )
        send_notification("notification", "CV parsed successfully", filename)

    except Exception as e:
        logging.error(f"Error processing CV: {e}")
        CV.objects.filter(id=document.id).update(sync_error=e, sync_status=SYNC_STATUS_FAILED)
        send_notification("notification", "CV processing failed", filename)

    pass
