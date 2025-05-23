from django.urls import path
from . import views

urlpatterns = [
    path('job', views.JobListView.as_view(), name='job_list'),
    path('job/<str:pk>/', views.JobDetailView.as_view(), name='job_detail'),
    path('job/create/', views.JobCreateView.as_view(), name='job_create'),
]
