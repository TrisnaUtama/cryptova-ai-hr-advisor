from django.shortcuts import render
from django.views import View
from core.utils import LoginCheckMixin


class DashboardView(LoginCheckMixin, View):
    def get(self, request):
        from apps.cv.models import CV
        from .models import (
            CvUploadedPerDay,
            CvProcessedPerDay,
            CvUploadedPerWeek,
            CvProcessedPerWeek,
            CvScoreAvgPerWeek,
            CvScoreDistribution,
        )

        # Total CVs
        total_cvs = CV.objects.count()
        # Total CVs difference (today - yesterday)
        today = CvUploadedPerDay.objects.order_by("-day").first()
        yesterday = (
            CvUploadedPerDay.objects.order_by("-day")[1]
            if CvUploadedPerDay.objects.count() > 1
            else None
        )
        total_cvs_difference = (
            f"+{today.total_uploaded - yesterday.total_uploaded}"
            if today and yesterday
            else "+0"
        )
        # average score for last week
        avg_score_obj = CvScoreAvgPerWeek.objects.order_by("-week").first()
        prev_avg_score_obj = (
            CvScoreAvgPerWeek.objects.order_by("-week")[1]
            if CvScoreAvgPerWeek.objects.count() > 1
            else None
        )
        avg_score = round(avg_score_obj.avg_score, 1) if avg_score_obj else 0
        avg_score_difference = (
            f"{avg_score - prev_avg_score_obj.avg_score:+.1f}"
            if avg_score_obj and prev_avg_score_obj
            else "+0.0"
        )
        # High scorers (score > 90)
        high_scorers = CV.objects.filter(overall_score__gte=90).count()
        # Processing rate (CV processed / uploaded this week)
        week_uploaded = CvUploadedPerWeek.objects.order_by("-week").first()
        week_processed = CvProcessedPerWeek.objects.order_by("-week").first()
        processing_rate = (
            round(
                week_processed.total_processed / week_uploaded.total_uploaded * 100, 1
            )
            if week_uploaded and week_uploaded.total_uploaded > 0 and week_processed
            else 0
        )
        # Weights (dummy, need to changed)
        exp_weight = 30
        skills_weight = 25
        achievements_weight = 15
        certificates_weight = 10
        gpa_weight = 20
        # Weekly data
        uploaded_cvs = list(
            CvUploadedPerWeek.objects.order_by("week").values_list(
                "total_uploaded", flat=True
            )
        )
        processed_cvs = list(
            CvProcessedPerWeek.objects.order_by("week").values_list(
                "total_processed", flat=True
            )
        )
        avg_scores = list(
            CvScoreAvgPerWeek.objects.order_by("week").values_list(
                "avg_score", flat=True
            )
        )
        # Labels chart mingguan: tanggal/bulan perminggu dari minggu terlama ke terbaru
        import datetime

        today = datetime.date.today()
        # Only 7 last weeks
        week_dates = list(
            CvUploadedPerWeek.objects.order_by("-week").values_list("week", flat=True)[
                :7
            ]
        )[::-1]
        week_labels = [d.strftime("%d/%m") for d in week_dates]
        # Daily data
        uploaded_cvs_per_day = list(
            CvUploadedPerDay.objects.order_by("day").values_list(
                "total_uploaded", flat=True
            )
        )
        parsed_cvs_per_day = list(
            CvProcessedPerDay.objects.order_by("day").values_list(
                "total_processed", flat=True
            )
        )
        # Top candidates (order by last 5 highest overall score)
        top_candidates_qs = CV.objects.filter(overall_score__isnull=False).order_by(
            "-overall_score"
        )[:5]
        top_candidates = [
            {
                "name": c.candidate_name,
                "email": c.candidate_email,
                "score": c.overall_score,
                "skills": ", ".join([s.skill for s in c.skills.all() if s.skill]),
            }
            for c in top_candidates_qs
        ]
        # Score distribution (separate into 5 score buckets)
        score_dist_raw = dict(
            CvScoreDistribution.objects.order_by("score_bucket").values_list(
                "score_bucket", "total"
            )
        )
        score_distribution = [score_dist_raw.get(i, 0) for i in range(1, 6)]
        context = {
            "total_cvs": total_cvs,
            "total_cvs_difference": total_cvs_difference,
            "avg_score": avg_score,
            "avg_score_difference": avg_score_difference,
            "high_scorers": high_scorers,
            "processing_rate": processing_rate,
            "exp_weight": exp_weight,
            "skills_weight": skills_weight,
            "achievements_weight": achievements_weight,
            "certificates_weight": certificates_weight,
            "gpa_weight": gpa_weight,
            "uploaded_cvs": uploaded_cvs,
            "processed_cvs": processed_cvs,
            "avg_scores": avg_scores,
            "uploaded_cvs_per_day": uploaded_cvs_per_day,
            "parsed_cvs_per_day": parsed_cvs_per_day,
            "top_candidates": top_candidates,
            "score_distribution": score_distribution,
            "week_labels": week_labels,
        }
        return render(request, "dashboard/index.html", context)
