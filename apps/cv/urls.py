from django.urls import path
from .views import CvDashboardView

urlpatterns = [
    path("cv/", CvDashboardView.as_view(), name="cv"),
]
