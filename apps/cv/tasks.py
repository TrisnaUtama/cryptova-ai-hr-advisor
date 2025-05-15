from huey.contrib.djhuey import task
import logging

from .models import CV
from core.methods import send_notification

from core.ai.mistral import mistral
from core.ai.prompt_manager import PromptManager, CVBase

logging.basicConfig(level=logging.INFO)


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
                - Basic info: name, email, phone, professional title
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
        logging.info(f"Extracted CV: {cv_data}")
        send_notification("notification", "CV parsed successfully", filename)

    except Exception as e:
        logging.error(f"Error processing CV: {e}")
        send_notification("notification", "CV processing failed", filename)

    pass
