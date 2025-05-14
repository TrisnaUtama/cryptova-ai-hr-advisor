from django.shortcuts import render
from django.views import View
from django.http import HttpResponse
from django.template.loader import render_to_string
from django.views.decorators.http import require_GET
from django.db import models

from core.utils import LoginCheckMixin

class CvDashboardView(LoginCheckMixin, View):
    def get(self, request):
        from .models import CV
        candidates_qs = CV.objects.all().order_by('-created_at')[:100]
        candidates = [
            {
                "candidate_name": c.candidate_name,
                "candidate_email": c.candidate_email,
                "overall_score": c.overall_score,
                "score": c.overall_score,  # jika ingin score lain, ganti field
                "created_at": c.created_at.strftime('%Y-%m-%d') if c.created_at else '',
            }
            for c in candidates_qs
        ]
        return render(request, "cv/index.html", {"candidates": candidates})

@require_GET
def search_candidates(request):
    from .models import CV
    q = request.GET.get("q", "").strip().lower()
    qs = CV.objects.all()
    if q:
        qs = qs.filter(
            models.Q(candidate_name__icontains=q) |
            models.Q(candidate_email__icontains=q)
        )
    candidates = [
        {
            "candidate_name": c.candidate_name,
            "candidate_email": c.candidate_email,
            "overall_score": c.overall_score,
            "score": c.overall_score,
            "created_at": c.created_at.strftime('%Y-%m-%d') if c.created_at else '',
        }
        for c in qs.order_by('-created_at')[:100]
    ]
    html = render_to_string("cv/candidate_rows_fragment.html", {"candidates": candidates})
    return HttpResponse(html)
