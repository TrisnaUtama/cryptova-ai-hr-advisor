from django.shortcuts import render
from django.views import View
from django.http import HttpResponse
from django.template.loader import render_to_string
from django.views.decorators.http import require_GET

from core.utils import LoginCheckMixin

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
            c for c in all_candidates
            if q in c["candidate_name"].lower() or q in c["candidate_email"].lower()
        ]
    else:
        candidates = all_candidates
    html = render_to_string("cv/candidate_rows_fragment.html", {"candidates": candidates})
    return HttpResponse(html)
