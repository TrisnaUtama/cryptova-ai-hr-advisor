from django.shortcuts import render
from django.views import View
from django.http import HttpResponse
from django.template.loader import render_to_string
from django.views.decorators.http import require_GET
from django.db import models
from django.core.paginator import Paginator

from core.utils import LoginCheckMixin


class CvDashboardView(LoginCheckMixin, View):
    def get(self, request):
        from .models import CV

        candidates_qs = CV.objects.all().order_by("-created_at")
        paginator = Paginator(candidates_qs, 7)
        page_number = request.GET.get("page", 1)
        page_obj = paginator.get_page(page_number)
        candidates = [
            {
                "candidate_name": c.candidate_name,
                "candidate_email": c.candidate_email,
                "overall_score": c.overall_score,
                "score": c.overall_score,  # jika ingin score lain, ganti field
                "created_at": c.created_at.strftime("%Y-%m-%d") if c.created_at else "",
            }
            for c in page_obj
        ]
        return render(
            request, "cv/index.html", {"candidates": candidates, "page_obj": page_obj}
        )


@require_GET
def search_candidates(request):
    from .models import CV
    from django.core.paginator import Paginator

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
            "candidate_name": c.candidate_name,
            "candidate_email": c.candidate_email,
            "overall_score": c.overall_score,
            "score": c.overall_score,
            "created_at": c.created_at.strftime("%Y-%m-%d") if c.created_at else "",
        }
        for c in page_obj
    ]
    html = render_to_string(
        "cv/candidate_rows_fragment.html",
        {"candidates": candidates, "page_obj": page_obj},
    )
    return HttpResponse(html)
