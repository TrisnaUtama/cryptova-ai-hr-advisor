from django.shortcuts import render
from django.template.loader import render_to_string
from django.views import View
from django.views.decorators.http import require_GET
from django.http import HttpResponse, JsonResponse
from django.core.exceptions import ValidationError
from django.contrib import messages
import logging


logger = logging.getLogger(__name__)

from core.utils import LoginCheckMixin

from .models import CV


class CvDashboardView(LoginCheckMixin, View):
    def get(self, request):
        candidates = [
            {
                "candidate_name": "Budi Santoso",
                "candidate_email": "budi@example.com",
                "overall_score": 92,
                "score": 92,
                "created_at": "2024-06-01",
            },
            {
                "candidate_name": "Siti Aminah",
                "candidate_email": "siti@example.com",
                "overall_score": 85,
                "score": 85,
                "created_at": "2024-06-02",
            },
            {
                "candidate_name": "Andi Wijaya",
                "candidate_email": "andi@example.com",
                "overall_score": 78,
                "score": 78,
                "created_at": "2024-06-03",
            },
        ]
        return render(request, "cv/index.html", {"candidates": candidates})

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
                    messages.error(request, f"Unsupported file type {uploaded_file.name}")
                    raise ValidationError(f"Unsupported file type: {uploaded_file.name}")

                cv = CV.objects.create(
                    user=user,
                    file=uploaded_file,
                    file_name=uploaded_file.name,
                )

                file_urls.append(cv.file.url)

            messages.success(request, "Files uploaded successfully")
            return JsonResponse(
                {"message": "Files uploaded successfully", "file_urls": file_urls},
                status=200
            )

        except ValidationError as ve:
            logger.warning(f"Validation error: {ve}")
            return JsonResponse({"error": str(ve)}, status=400)

        except Exception as e:
            logger.exception("Unexpected error during CV upload")
            return JsonResponse({
                "error": "An unexpected error occurred while uploading the files.",
                "details": str(e)
            }, status=500)

@require_GET
def search_candidates(request):
    q = request.GET.get("q", "").strip().lower()
    all_candidates = [
        {
            "candidate_name": "Budi Santoso",
            "candidate_email": "budi@example.com",
            "overall_score": 92,
            "score": 92,
            "created_at": "2024-06-01",
        },
        {
            "candidate_name": "Siti Aminah",
            "candidate_email": "siti@example.com",
            "overall_score": 85,
            "score": 85,
            "created_at": "2024-06-02",
        },
        {
            "candidate_name": "Andi Wijaya",
            "candidate_email": "andi@example.com",
            "overall_score": 78,
            "score": 78,
            "created_at": "2024-06-03",
        },
    ]
    if q:
        candidates = [
            c
            for c in all_candidates
            if q in c["candidate_name"].lower() or q in c["candidate_email"].lower()
        ]
    else:
        candidates = all_candidates
    html = render_to_string(
        "cv/candidate_rows_fragment.html", {"candidates": candidates}
    )
    return HttpResponse(html)



