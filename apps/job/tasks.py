from huey.contrib.djhuey import task
from apps.cv.models import CV
from apps.job.models import Job, JobCategory
from core.ai.prompt_manager import PromptManager
from core.ai.system_prompt import CV_MATCHERS
from core.ai.structured_model import ListApplicantsBase
from django.forms.models import model_to_dict
from apps.job.models import JobApplication, JOB_STATUS_PROCESS, JOB_STATUS_CLOSED
from apps.cv.utils import clean_null_bytes
from urllib.parse import urlencode
from core.ai.mistral import mistral
from core.ai.system_prompt import JOB_DESCRIPTION_PARSER
from core.ai.structured_model import JobDescriptionBase
from PIL import Image
import os
from core.methods import send_notification

@task()
def match_cv_with_job(job_id):
    job = Job.objects.get(id=job_id)
    job_dict = model_to_dict(job)
    cvs = CV.objects.filter(candidate_category=job.job_category.name).values("id", "candidate_name","candidate_title","candidate_category","description")
    cv_list = list(cvs)
    
    job.status = JOB_STATUS_PROCESS
    job.save()

    print(f"Here's the job posting: {job_dict} \n\n Here's the list of candidate CVs: {cv_list}")

    pm = PromptManager()
    pm.add_message("system", CV_MATCHERS)
    pm.add_message("user", f"Here's the job posting: {job_dict} \n\n Here's the list of candidate CVs: {cv_list}")
    response = pm.generate_structured(ListApplicantsBase)

    print(response)

    for match in response.get("applicants",[]):
        cv = CV.objects.get(id=clean_null_bytes(match.get("cv_id")))
        JobApplication.objects.create(
            job=job,
            cv=cv,
            matching_score=match.get("matching_score"),
            reason=clean_null_bytes(match.get("reason"))
        )

    job.status = JOB_STATUS_CLOSED
    job.save()

@task()
def process_job_file(file_path, file_name, user_id):
    """
    Process uploaded job description file using OCR and AI parsing
    """
    try:
        send_notification(
            "notification",
            f"Processing job file: {file_name}",
            f"Job file {file_name} processing started.",
        )

        # Check if file is an image and convert to PDF
        file_extension = os.path.splitext(file_name)[1].lower()
        processed_file_path = file_path
        
        if file_extension in ['.jpg', '.jpeg', '.png']:
            # Convert image to PDF
            image = Image.open(file_path)
            # Convert RGBA to RGB if necessary
            if image.mode == 'RGBA':
                image = image.convert('RGB')
            
            # Create PDF from image
            pdf_path = file_path.replace(file_extension, '.pdf')
            image.save(pdf_path, 'PDF')
            processed_file_path = pdf_path
            print(f"Converted image {file_name} to PDF for OCR processing")

        # Upload to Mistral for OCR
        try:
            with open(processed_file_path, "rb") as f_content:
                uploaded_pdf = mistral.files.upload(
                    file={
                        "file_name": file_name.replace(file_extension, '.pdf') if file_extension in ['.jpg', '.jpeg', '.png'] else file_name,
                        "content": f_content,
                    },
                    purpose="ocr",
                )
            
            signed_url = mistral.files.get_signed_url(file_id=uploaded_pdf.id)
            print(f"Signed URL for job file {file_name}: {signed_url.url}")
            
            send_notification(
                "notification", "Job file uploaded to Mistral", f"{file_name}"
            )
        except Exception as e:
            send_notification(
                "notification",
                f"Failed to upload job file: {file_name}",
                "error",
            )
            raise
        
        # Process with OCR
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
                print(f"OCR for job file {file_name} resulted in empty content.")
                send_notification(
                    "notification",
                    f"Job file OCR failed: {file_name}",
                    "Could not extract text from file.",
                )
                return

            print(f"Extracted content length for job file {file_name}: {len(content)} characters")
            send_notification(
                "notification", "Job file OCR successful", f"{file_name}"
            )
        except Exception:
            send_notification(
                "notification",
                f"Job file OCR failed: {file_name}",
                "error",
            )
            raise

        # Extract job information using AI
        categories = JobCategory.objects.all().values("name", "description")
        pm = PromptManager()
        pm.add_message("system", JOB_DESCRIPTION_PARSER.format(job_categories=list(categories)))
        pm.add_message("user", f"Extract job information from this content: {content}")
        job_data_response = pm.generate_structured(JobDescriptionBase)

        # Convert to dict if it's a pydantic model or similar object
        if hasattr(job_data_response, 'dict'):
            job_data = job_data_response.dict()
        elif hasattr(job_data_response, '__dict__'):
            job_data = job_data_response.__dict__
        else:
            job_data = job_data_response

        print(f"Extracted job data: {job_data}")

        # Create query parameters for job_create
        query_params = {
            'title': str(job_data.get('title', '')),
            'description': str(job_data.get('description', '')),
            'location': str(job_data.get('location', '')),
            'salary_min': str(job_data.get('salary_min', '')),
            'salary_max': str(job_data.get('salary_max', '')),
            'job_category': str(job_data.get('job_category_name', '')),
            'min_experience': str(job_data.get('min_experience', '')),
            'min_education': str(job_data.get('min_education', '')),
            'company_name': str(job_data.get('company_name', '')),
            'company_description': str(job_data.get('company_description', ''))
        }
        
        # Filter out empty values
        query_params = {k: v for k, v in query_params.items() if v}
        redirect_url = f"/job/create/new?{urlencode(query_params)}"
        
        send_notification(
            "job_processed", file_name, redirect_url
        )

    except Exception as e:
        print(f"Error processing job file {file_name}: {str(e)}")
        send_notification(
            "notification",
            f"Job file processing failed: {file_name}",
            "error",
        )
    finally:
        # Clean up temp files
        if os.path.exists(file_path):
            os.unlink(file_path)
        # Also clean up converted PDF if it exists
        if file_extension in ['.jpg', '.jpeg', '.png']:
            pdf_path = file_path.replace(file_extension, '.pdf')
            if os.path.exists(pdf_path):
                os.unlink(pdf_path)

