import logging

from django.contrib import messages
from django.core.exceptions import ValidationError
from django.core.paginator import Paginator
from django.db import models
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, render
from django.template.loader import render_to_string
from django.views import View
from django.views.decorators.http import require_GET, require_POST

from core.utils import LoginCheckMixin

from .models import CV, SYNC_STATUS_PROCESSING
from .tasks import process_cv

logger = logging.getLogger(__name__)


class CvDashboardView(LoginCheckMixin, View):
    def get(self, request):
        candidates_qs = CV.objects.all().order_by("-created_at")
        paginator = Paginator(candidates_qs, 7)
        page_number = request.GET.get("page", 1)
        page_obj = paginator.get_page(page_number)
        candidates = []
        for c in page_obj:
            score = c.overall_score
            if c.overall_score is None:
                score = 0
            candidates.append(
                {
                    "id": c.id,
                    "candidate_name": c.candidate_name,
                    "candidate_email": c.candidate_email,
                    "overall_score": score,
                    "score": score,  # jika ingin score lain, ganti field
                    "sync_status": c.sync_status,
                    "created_at": (
                        c.created_at.strftime("%Y-%m-%d") if c.created_at else ""
                    ),
                }
            )
        return render(
            request, "cv/index.html", {"candidates": candidates, "page_obj": page_obj}
        )

    def post(self, request):
        try:
            files = request.FILES.getlist("cv_file[]")
            if not files:
                messages.error(request, "No files were uploaded.")
                return JsonResponse({"error": "No files were uploaded."}, status=400)

            user = request.user
            file_urls = []

            for uploaded_file in files:
                if not uploaded_file.name.lower().endswith((".pdf", ".doc", ".docx")):
                    messages.error(
                        request, f"Unsupported file type {uploaded_file.name}"
                    )
                    raise ValidationError(
                        f"Unsupported file type: {uploaded_file.name}"
                    )

                cv = CV.objects.create(
                    user=user,
                    file=uploaded_file,
                    file_name=uploaded_file.name,
                )
                process_cv(document=cv)

                file_urls.append(cv.file.url)

            messages.success(request, "Files uploaded successfully")
            return JsonResponse(
                {"message": "Files uploaded successfully", "file_urls": file_urls},
                status=200,
            )

        except ValidationError as ve:
            logger.warning(f"Validation error: {ve}")
            return JsonResponse({"error": str(ve)}, status=400)

        except Exception as e:
            logger.exception("Unexpected error during CV upload")
            return JsonResponse(
                {
                    "error": "An unexpected error occurred while uploading the files.",
                    "details": str(e),
                },
                status=500,
            )


class CVDetail(View):
    def get(self, request, id):
        cv = get_object_or_404(CV, id=id)

        scores = [
            {"label": "Overall", "value": cv.overall_score},
            {"label": "Experience", "value": cv.experience_score},
            {"label": "Skills", "value": cv.skill_score},
            {"label": "Achievements", "value": cv.achievement_score},
        ]

        return render(request, "cv/detail_candidate.html", context={
            "cv": cv,
            "scores": scores
        })

@require_GET
def search_candidates(request):
    q = request.GET.get("q", "").strip().lower()
    page_number = request.GET.get("page", 1)
    qs = CV.objects.all()
    if q:
        qs = qs.filter(
            models.Q(candidate_name__icontains=q)
            | models.Q(candidate_email__icontains=q)
        )
    paginator = Paginator(qs.order_by("-created_at"), 7)
    page_obj = paginator.get_page(page_number)
    candidates = [
        {
            "id": c.id,
            "candidate_name": c.candidate_name,
            "candidate_email": c.candidate_email,
            "overall_score": c.overall_score,
            "score": c.overall_score,
            "sync_status": c.sync_status,
            "created_at": c.created_at.strftime("%Y-%m-%d") if c.created_at else "",
        }
        for c in page_obj
    ]
    html = render_to_string(
        "cv/candidate_rows_fragment.html",
        {"candidates": candidates, "page_obj": page_obj},
    )
    return HttpResponse(html)

@require_POST
def reprocess_cv(request, id):
    cv = get_object_or_404(CV, id=id)

    # Delete previously extracted data
    cv.skills.all().delete()
    cv.educations.all().delete()
    cv.work_experiences.all().delete()
    cv.achievements.all().delete()
    cv.languages.all().delete()

    # Reset fields
    cv.raw_output = None
    cv.overall_score = None
    cv.experience_score = None
    cv.achievement_score = None
    cv.skill_score = None
    cv.sync_status = SYNC_STATUS_PROCESSING
    cv.sync_error = None
    cv.save()

    # Trigger async reprocessing
    process_cv(document=cv)

    return JsonResponse({"status": "reprocessing started"})