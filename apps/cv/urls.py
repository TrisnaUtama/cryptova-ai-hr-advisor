from django.urls import path
from .views import CvDashboardView, search_candidates

urlpatterns = [
    path("cv/", CvDashboardView.as_view(), name="cv"),
    path('cv/search/', search_candidates, name='cv_search_candidates'),
]
