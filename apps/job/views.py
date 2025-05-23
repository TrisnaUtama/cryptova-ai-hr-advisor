from django.shortcuts import render, redirect
from django.views import View
from django.contrib import messages
import logging
import markdown

from apps.job.models import JobCategory, Job
from core.utils import LoginCheckMixin

logger = logging.getLogger(__name__)

# Create your views here.
class JobListView(LoginCheckMixin, View):
    def get(self, request):
        jobs = Job.objects.filter(user=request.user)
        return render(request, 'job/job_list.html', {'jobs': jobs})

class JobDetailView(LoginCheckMixin, View):
    def get(self, request, pk):
        job = Job.objects.get(id=pk)
        description_html = markdown.markdown(job.description)
        return render(request, 'job/job_detail.html', {'job': job, 'description_html': description_html})

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
                messages.error(request, 'Please fill in all required fields.')
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
            messages.success(request, 'Job posting created successfully!')
            return redirect('job_list')

        except Exception as e:
            logger.error(f"Error creating job posting: {str(e)}", exc_info=True)
            messages.error(request, f'Error creating job posting: {str(e)}')
            return redirect('job_create')