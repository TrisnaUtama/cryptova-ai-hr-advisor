import os
from django.contrib import admin
from django.urls import path, include
from core.consumer import NotificationConsumer
from django.conf import settings

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("apps.auths.urls")),
    path("", include("apps.cv.urls")),
    path("", include("apps.dashboard.urls")),
    path("", include("apps.chat.urls")),
]

websocket_urlpatterns = [
    path("ws/notifications/", NotificationConsumer.as_asgi()),
]

if os.getenv("DEBUG") == "True":
    from django.conf.urls.static import static
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
