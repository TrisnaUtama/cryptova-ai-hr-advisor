from django.http import JsonResponse
from django.shortcuts import render, redirect
from django.views import View
from apps.job.models import JobCategory, Job
from apps.job.tasks import match_cv_with_job
from core.utils import LoginCheckMixin
from apps.chat.models import ChatSession
from apps.job.tasks import process_job_file
import logging
import markdown
import tempfile

logger = logging.getLogger(__name__)

# Create your views here.
class JobListView(LoginCheckMixin, View):
    def get(self, request):
        jobs = Job.objects.filter(user=request.user)
        return render(request, 'job/job_list.html', {'jobs': jobs})

class JobDetailView(LoginCheckMixin, View):
    def get(self, request, pk):
        job = Job.objects.get(id=pk)
        cv_id_list = []
        list_applicants = job.jobapplication_set.all()
        for applicant in list_applicants:
            cv_id_list.append({
                "user_id" : {
                    "$eq": applicant.cv.id
                }
            })

            print(cv_id_list)
        
        session_id = request.GET.get("session_id")
        if session_id:
            session = ChatSession.objects.get(id=session_id, user=request.user)
            chats = list(session.chats.order_by("created_at"))
        else:
            chats = []
        description_html = markdown.markdown(job.description)
        return render(request, 'job/job_detail.html', {'job': job, 'description_html': description_html, 'chats': chats, 'session_id': session_id})

class JobCreateView(LoginCheckMixin, View):
    def get(self, request):
        categories = JobCategory.objects.all()
        return render(request, 'job/job_create.html', {'categories': categories})
    
    def post(self, request):
        try:
            logger.debug(f"Form data received: {request.POST}")
            
            # Get form data
            title = request.POST.get('title')
            description = request.POST.get('description')
            location = request.POST.get('location')
            salary_min = request.POST.get('salary_min')
            salary_max = request.POST.get('salary_max')
            job_category_id = request.POST.get('job_category')
            min_experience = request.POST.get('min_experience')
            min_education = request.POST.get('min_education')
            company_name = request.POST.get('company_name')
            company_description = request.POST.get('company_description')

            # Log received data
            logger.debug(f"Parsed form data: title={title}, location={location}, category={job_category_id}")

            # Validate required fields
            if not all([title, description, location, salary_min, salary_max, 
                       job_category_id, min_experience, min_education, company_name]):
                missing_fields = [field for field, value in {
                    'title': title,
                    'description': description,
                    'location': location,
                    'salary_min': salary_min,
                    'salary_max': salary_max,
                    'job_category': job_category_id,
                    'min_experience': min_experience,
                    'min_education': min_education,
                    'company_name': company_name
                }.items() if not value]
                logger.warning(f"Missing required fields: {missing_fields}")
                # messages.error(request, 'Please fill in all required fields.')
                return redirect('job_create')

            # Create new job posting
            job = Job.objects.create(
                user=request.user,
                title=title,
                description=description,
                location=location,
                salary_min=float(salary_min),
                salary_max=float(salary_max),
                job_category_id=job_category_id,
                min_experience=min_experience,
                min_education=min_education,
                company_name=company_name,
                company_description=company_description or ''
            )

            logger.info(f"Job created successfully: {job.id}")
            # messages.success(request, 'Job posting created successfully!')
            match_cv_with_job(job.id)
            return redirect('job_list')

        except Exception as e:
            logger.error(f"Error creating job posting: {str(e)}", exc_info=True)
            # messages.error(request, f'Error creating job posting: {str(e)}')
            return redirect('job_create')

class ProcessJobFileView(LoginCheckMixin, View):
    def post(self, request):
        try:
            uploaded_file = request.FILES.get('job_file')
            if not uploaded_file:
                return JsonResponse({"error": "No file uploaded."}, status=400)

            # Save file temporarily
            with tempfile.NamedTemporaryFile(delete=False, suffix=f"_{uploaded_file.name}") as temp_file:
                for chunk in uploaded_file.chunks():
                    temp_file.write(chunk)
                temp_file_path = temp_file.name

            # Trigger async task
            process_job_file(temp_file_path, uploaded_file.name, request.user.id)
            
            return JsonResponse({
                "success": True,
                "message": "Job file processing started. Please wait for completion notification."
            })

        except Exception as e:
            logger.error(f"Error processing job file: {str(e)}", exc_info=True)
            return JsonResponse({"error": f"Error processing file: {str(e)}"}, status=500)