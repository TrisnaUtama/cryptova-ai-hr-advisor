import logging

from huey.contrib.djhuey import task

from core.ai.mistral import mistral
from core.ai.chroma import (
    chroma,
    openai_ef,
)
from core.ai.prompt_manager import PromptManager
from core.ai.structured_model import CVBase, DocumentCheck, ListJobMatchesBase
from core.ai.system_prompt import DOCUMENT_CHECKER, CV_PARSER
from core.methods import send_notification

from langchain_experimental.text_splitter import SemanticChunker
from langchain_openai.embeddings import (
    OpenAIEmbeddings,
)

from .utils import delete_cv_from_sql_and_vector_db, extract_and_save_cv_data
from apps.job.models import JobCategory

from .models import (
    CV,
    SYNC_STATUS_FAILED,
    SYNC_STATUS_PROCESSING,
    SYNC_STATUS_COMPLETED,
)

from apps.job.models import Job, JobApplication, JOB_STATUS_CLOSED, JOB_STATUS_CREATED
from django.forms.models import model_to_dict
from apps.cv.utils import clean_null_bytes

from core.ai.system_prompt import JOB_MATCHERS

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

CV_COLLECTION_NAME = "all_cvs_collection"


@task()
def process_cv(document: CV):
    filename = document.file.name
    cv_id_str = str(document.id)

    try:
        CV.objects.filter(id=document.id).update(sync_status=SYNC_STATUS_PROCESSING)
        send_notification(
            "notification",
            f"Processing: {filename}",
            f"CV {cv_id_str} processing started.",
        )

        # Upload the CV to Mistral
        try:
            with open(f"media/{filename}", "rb") as f_content:
                uploaded_pdf = mistral.files.upload(
                    file={
                        "file_name": filename,
                        "content": f_content,  # Pass file object
                    },
                    purpose="ocr",
                )
            signed_url = mistral.files.get_signed_url(file_id=uploaded_pdf.id)
            logger.info(f"Signed URL for {cv_id_str}: {signed_url.url}")
            send_notification(
                "notification", "CV uploaded to Mistral", f"{filename} ({cv_id_str})"
            )
        except Exception as e:
            logger.error(
                f"Error uploading file {filename} ({cv_id_str}) to Mistral: {e}"
            )
            raise

        # Process the document with Mistral OCR
        try:
            ocr_response = mistral.ocr.process(
                model="mistral-ocr-latest",
                document={"type": "document_url", "document_url": signed_url.url},
                include_image_base64=True,
            )
            content = "".join(
                page.get("markdown", "")
                for page in ocr_response.dict().get("pages", [])
            )
            if not content.strip():
                logger.warning(
                    f"OCR for {filename} ({cv_id_str}) resulted in empty content."
                )

            logger.info(
                f"Extracted content length for {filename} ({cv_id_str}): {len(content)} characters"
            )
            send_notification(
                "notification", "CV OCR successful", f"{filename} ({cv_id_str})"
            )
        except Exception as e:
            logger.error(f"Error processing {filename} ({cv_id_str}) with OCR: {e}")
            raise

        # Check if the document is a CV
        pm_check = PromptManager()
        pm_check.add_message("system", DOCUMENT_CHECKER)
        pm_check.add_message("user", f"Check if this is a CV: {content}")
        check_result = pm_check.generate_structured(DocumentCheck)

        if not check_result.get("is_cv"):
            logger.info(
                f"Document {filename} ({cv_id_str}) is not a CV. Deleting record."
            )
            delete_cv_from_sql_and_vector_db(
                document, CV_COLLECTION_NAME, only_sql=True
            )
            send_notification(
                "notification",
                "Document is not a CV",
                f"{filename} ({cv_id_str}) was rejected.",
            )
            return

        # Continue processing if it is a CV: Extract structured data
        categories = JobCategory.objects.all().values("name", "description")
        pm_extract = PromptManager()
        pm_extract.add_message("system", CV_PARSER.format(job_categories=list(categories)))
        pm_extract.add_message("user", f"Extract information from this CV: {content}")
        cv_data_payload = pm_extract.generate_structured(CVBase)

        extract_and_save_cv_data(document, cv_data_payload, content)
        document.refresh_from_db()

        logger.info(
            f"Successfully parsed and saved CV data for {cv_data_payload.get('candidate_name')} ({cv_id_str})"
        )
        send_notification(
            "notification", "CV parsed and saved", f"{filename} ({cv_id_str})"
        )

        # Get or Create the single, global ChromaDB collection
        send_notification(
            "notification", "Accessing vector collection", f"{filename} ({cv_id_str})"
        )
        all_cvs_collection = chroma.get_or_create_collection(
            name=CV_COLLECTION_NAME, embedding_function=openai_ef
        )

        # IMPORTANT: Delete old chunks for CV if it's being reprocessed
        try:
            all_cvs_collection.delete(where={"cv_id": cv_id_str})
            logger.info(
                f"Deleted existing chunks for CV ID {cv_id_str} from {CV_COLLECTION_NAME}."
            )
        except Exception as e:
            logger.warning(
                f"Could not delete old chunks for CV ID {cv_id_str} (may be first processing or collection empty): {e}"
            )

        # Chunk the document content
        send_notification(
            "notification",
            "Splitting document into chunks",
            f"{filename} ({cv_id_str})",
        )
        splitter = SemanticChunker(OpenAIEmbeddings())
        langchain_documents = splitter.create_documents([content])

        if not langchain_documents:
            logger.warning(
                f"No chunks created for CV ID {cv_id_str}. Content length: {len(content)}."
            )
            # Update status, but consider complete as structured data is saved.
            CV.objects.filter(id=document.id).update(
                sync_status=SYNC_STATUS_COMPLETED,
                sync_error="No content chunks generated for vectorization.",
            )
            send_notification(
                "done", filename, f"CV {cv_id_str} processed (no content chunks)."
            )
            return

        send_notification(
            "notification",
            f"Creating embeddings for {len(langchain_documents)} chunks",
            f"{filename} ({cv_id_str})",
        )

        chunk_texts = []
        chunk_ids = []
        chunk_metadatas = []

        # Prepare metadata, ensure all keys from cv_data_payload are accessed safely
        user_id_for_meta = (
            str(document.user.id)
            if hasattr(document, "user") and document.user
            else str(document.user_id)
        )

        # Helper function to safely join list items into a string or return None
        def join_list_to_str(data_list):
            if data_list and isinstance(data_list, list):
                return ", ".join(filter(None, data_list))
            return None

        base_metadata = {
            "cv_id": cv_id_str,
            "user_id": user_id_for_meta,
            "candidate_name": cv_data_payload.get("candidate_name"),
            "candidate_email": cv_data_payload.get("candidate_email"),
            "candidate_phone": cv_data_payload.get("candidate_phone"),
            "candidate_title": cv_data_payload.get("candidate_title"),
            "description_overall": cv_data_payload.get("description"),
            "candidate_category": cv_data_payload.get("candidate_category"),
            "overall_score": float(cv_data_payload.get("overall_score"))
            if cv_data_payload.get("overall_score") is not None
            else None,
            "experience_score": float(cv_data_payload.get("experience_score"))
            if cv_data_payload.get("experience_score") is not None
            else None,
            "achievement_score": float(cv_data_payload.get("achievement_score"))
            if cv_data_payload.get("achievement_score") is not None
            else None,
            "skill_score": float(cv_data_payload.get("skill_score"))
            if cv_data_payload.get("skill_score") is not None
            else None,
            "skills_list_str": join_list_to_str(
                [s.get("skill") for s in cv_data_payload.get("skills", []) if s]
            ),
            "degrees_list_str": join_list_to_str(
                [e.get("degree") for e in cv_data_payload.get("education", []) if e]
            ),
            "institutions_list_str": join_list_to_str(
                [
                    e.get("institution")
                    for e in cv_data_payload.get("education", [])
                    if e
                ]
            ),
            "companies_list_str": join_list_to_str(
                [
                    w.get("company")
                    for w in cv_data_payload.get("workexperience", [])
                    if w
                ]
            ),
            "positions_list_str": join_list_to_str(
                [
                    w.get("position")
                    for w in cv_data_payload.get("workexperience", [])
                    if w
                ]
            ),
            "languages_list_str": join_list_to_str(
                [l.get("language") for l in cv_data_payload.get("language", []) if l]
            ),
            "achievement_titles_str": join_list_to_str(
                [a.get("title") for a in cv_data_payload.get("achievements", []) if a]
            ),
        }
        # Clean metadata: remove keys with None values. Empty strings are fine.
        cleaned_metadata = {k: v for k, v in base_metadata.items() if v is not None}

        for i, doc_chunk in enumerate(langchain_documents):
            chunk_texts.append(doc_chunk.page_content)
            chunk_ids.append(f"{cv_id_str}_{i}")
            chunk_metadatas.append(cleaned_metadata.copy())

        if chunk_texts:
            all_cvs_collection.add(
                documents=chunk_texts, ids=chunk_ids, metadatas=chunk_metadatas
            )
            logger.info(
                f"Added {len(chunk_texts)} chunks for CV ID {cv_id_str} to {CV_COLLECTION_NAME}."
            )
        else:
            logger.warning(f"No valid chunks to add for CV ID {cv_id_str}.")

        send_notification(
            "done", filename, f"CV {cv_id_str} processing completed successfully."
        )

        # Trigger job matching after CV processing is completed
        match_job_with_cv(document.id)

    except Exception as e:
        logger.error(
            f"Critical error processing CV {filename} ({cv_id_str}): {str(e)}",
            exc_info=True,
        )
        CV.objects.filter(id=document.id).update(
            sync_error=str(e)[:1024], sync_status=SYNC_STATUS_FAILED
        )
        send_notification(
            "notification",
            f"CV processing failed for {filename} ({cv_id_str})",
            "error",
        )


@task()
def match_job_with_cv(cv_id):
    """
    For a given CV, match it against all open jobs in the same category.
    """
    try:
        cv = CV.objects.get(id=cv_id)
        if cv.sync_status != SYNC_STATUS_COMPLETED:
            logger.info(f"CV {cv_id} not completed, skipping job matching.")
            return

        jobs = Job.objects.filter(
            job_category__name=cv.candidate_category,
            status__in=[JOB_STATUS_CREATED, JOB_STATUS_CLOSED]
        )

        print(f"Jobs for CV {cv_id}: {jobs}")

        job_list = []
        for job in jobs:
            job_dict = model_to_dict(job)
            job_dict["id"] = job.id 
            job_list.append(job_dict)

        cv_dict = {
            "id": cv.id,
            "candidate_name": cv.candidate_name,
            "candidate_title": cv.candidate_title,
            "candidate_category": cv.candidate_category,
            "description": cv.description,
        }

        pm = PromptManager()
        pm.add_message("system", JOB_MATCHERS)
        pm.add_message("user", f"Here's the candidate CV: {cv_dict} \n\n Here's the list of job postings: {job_list}")
        response = pm.generate_structured(ListJobMatchesBase)

        for match in response.get("jobs", []):
            try:
                job = Job.objects.get(id=clean_null_bytes(match.get("job_id")))
                if float(match.get("matching_score", 0)) > 40:
                    JobApplication.objects.get_or_create(
                        job=job,
                        cv=cv,
                        defaults={
                            "matching_score": match.get("matching_score"),
                            "reason": clean_null_bytes(match.get("reason"))
                        }
                    )
            except Exception as e:
                logger.error(f"Error creating JobApplication for CV {cv_id} and job {match.get('job_id')}: {e}")
    except Exception as e:
        logger.error(f"Error in match_job_with_cv for CV {cv_id}: {e}")