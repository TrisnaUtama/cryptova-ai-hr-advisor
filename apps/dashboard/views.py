from django.shortcuts import render
from django.views import View


class DashboardView(View):
    def get(self, request):
        context = {
            "total_cvs": 1284,
            "avg_score": 82.5,
            "high_scorers": 87,
            "processing_rate": 99.2,
            "top_candidates": [
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
            ],
        }
        return render(request, "dashboard/index.html", context)
