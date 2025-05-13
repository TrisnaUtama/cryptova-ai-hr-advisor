from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("apps.auths.urls")),
    path("", include("apps.cv.urls")),
    path("", include("apps.dashboard.urls")),
]
