import logging

from huey.contrib.djhuey import task

from core.ai.mistral import mistral
from core.ai.prompt_manager import PromptManager
from core.ai.structured_model import CVBase, DocumentCheck
from core.ai.system_prompt import DOCUMENT_CHECKER, CV_PARSER
from core.methods import send_notification

from .utils import delete_cv_and_related, extract_and_save_cv_data

from .models import (
    CV,
    SYNC_STATUS_FAILED,
    SYNC_STATUS_PROCESSING,
    SYNC_STATUS_COMPLETED
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@task()
def process_cv(document: CV):
    filename = document.file.name

    try:
        # Update status to processing
        CV.objects.filter(id=document.id).update(sync_status=SYNC_STATUS_PROCESSING)

        # Upload the CV to Mistral
        try:
            uploaded_pdf = mistral.files.upload(
                file={
                    "file_name": filename,
                    "content": open(f"media/{filename}", "rb"),
                },
                purpose="ocr",
            )

            # Get the signed URL for the uploaded file
            signed_url = mistral.files.get_signed_url(file_id=uploaded_pdf.id)
            logger.info(f"Signed URL: {signed_url}")
            send_notification("notification", "CV uploaded successfully", filename)

        except Exception as e:
            logger.error(f"Error uploading file to Mistral: {e}")
            raise

        # Process the document with Mistral OCR
        try:
            ocr_response = mistral.ocr.process(
                model="mistral-ocr-latest",
                document={"type": "document_url", "document_url": signed_url.url},
                include_image_base64=True,
            )

            # Extract content from OCR response
            content = ""
            for page in ocr_response.dict().get("pages", []):
                content += page.get("markdown")

            logger.info(f"Extracted document content length: {len(content)} characters")
            send_notification("notification", "CV processed successfully", filename)

        except Exception as e:
            logger.error(f"Error processing document with OCR: {e}")
            raise

        # Check if the document is a CV
        pm = PromptManager()
        pm.add_message(
            "system",
            DOCUMENT_CHECKER,
        )
        pm.add_message("user", f"Check if this is a CV: {content}")
        check_result = pm.generate_structured(DocumentCheck)

        # If not a CV, delete and return early
        if not check_result.get("is_cv"):
            logger.info("Document is not a CV - deleting record")
            delete_cv_and_related(document)
            send_notification("notification", "Document is not a CV", filename, document.sync_status)
            return

        # Continue processing if it is a CV
        pm = PromptManager()
        pm.add_message(
            "system",
            CV_PARSER,
        )
        pm.add_message("user", f"Extract information from this CV: {content}")

        cv_data = pm.generate_structured(CVBase)
        print(cv_data)
        extract_and_save_cv_data(document, cv_data)

        logger.info(f"Successfully processed CV for {cv_data.get('candidate_name')}")
        send_notification("notification", "CV parsed successfully", filename)

    except Exception as e:
        logger.error(f"Error processing CV: {str(e)}", exc_info=True)
        CV.objects.filter(id=document.id).update(
            sync_error=str(e), sync_status=SYNC_STATUS_FAILED
        )
        send_notification("notification", "CV processing failed", filename)
