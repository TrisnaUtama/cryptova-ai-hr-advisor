from django.shortcuts import render
from django.views import View
from core.utils import LoginCheckMixin


class DashboardView(LoginCheckMixin, View):
    def get(self, request):
        context = {
            "total_cvs": 1284,
            "total_cvs_difference": "+24",
            "avg_score": 82.5,
            "avg_score_difference": "-1.2",
            "high_scorers": 87,
            "processing_rate": 99.2,
            "exp_weight": 30,
            "skills_weight": 25,
            "achievements_weight": 15,
            "certificates_weight": 10,
            "gpa_weight": 20,
            "uploaded_cvs": [15, 22, 21, 27, 19, 17, 14],
            "processed_cvs": [14, 21, 20, 25, 18, 16, 13],
            "avg_scores": [82, 80, 81, 85, 83, 84, 82],
            "uploaded_cvs_per_day": [45, 50, 38, 65, 47, 10, 8],
            "parsed_cvs_per_day": [44, 49, 37, 63, 46, 9, 7],
            "top_candidates": [
                {
                    "name": "Emily Davis",
                    "email": "emily.davis@example.com",
                    "score": 95.1,
                    "skills": "Cloud Architecture, Distributed Systems",
                },
                {
                    "name": "Sarah Johnson",
                    "email": "sarah.j@example.com",
                    "score": 92.3,
                    "skills": "React, Node.js, AWS",
                },
                {
                    "name": "Jessica Brown",
                    "email": "j.brown@example.com",
                    "score": 89.4,
                    "skills": "Python, Data Science, Machine Learning",
                },
                {
                    "name": "John Smith",
                    "email": "john.smith@example.com",
                    "score": 87.5,
                    "skills": "Python, JavaScript, Cloud Technologies",
                },
                {
                    "name": "Robert Wilson",
                    "email": "r.wilson@example.com",
                    "score": 81.7,
                    "skills": "Java, Spring Boot, Microservices",
                },
            ],
            "score_distribution": [70, 140, 250, 190, 120, 80],
        }
        return render(request, "dashboard/index.html", context)
