from django.shortcuts import render
from django.views import View


class DashboardView(View):
    def get(self, request):
        context = {
            "total_cvs": 1284,
            "avg_score": 82.5,
            "high_scorers": 87,
            "processing_rate": 99.2,
        }
        return render(request, "dashboard/index.html", context)
