from huey.contrib.djhuey import task
from apps.cv.models import CV
from apps.job.models import Job
from core.ai.prompt_manager import PromptManager
from core.ai.system_prompt import CV_MATCHERS
from core.ai.structured_model import ListApplicantsBase
from django.forms.models import model_to_dict
from apps.job.models import JobApplication, JOB_STATUS_PROCESS, JOB_STATUS_CLOSED
from apps.cv.utils import clean_null_bytes

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
        
