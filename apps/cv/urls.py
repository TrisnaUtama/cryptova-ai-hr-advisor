from django.urls import path

from .views import CvDashboardView, CVDetail, search_candidates, reprocess_cv

urlpatterns = [
    path("cv/", CvDashboardView.as_view(), name="cv"),
    path("cv/search/", search_candidates, name="cv_search_candidates"),
    path("cv/<str:id>/reprocess/", reprocess_cv, name="reprocess_cv"),
    path("cv/<str:id>/", CVDetail.as_view(), name="detail_candidate"),
]
