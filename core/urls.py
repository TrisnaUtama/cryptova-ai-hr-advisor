import os

from django.conf import settings
from django.contrib import admin
from django.urls import include, path
from django.http import HttpResponse

from core.consumer import ChatConsumer, NotificationConsumer

def health_check(request):
    return HttpResponse("OK")

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("apps.auths.urls")),
    path("", include("apps.cv.urls")),
    path("", include("apps.dashboard.urls")),
    path("", include("apps.chat.urls")),
    path('health/', health_check, name='health_check'),
]

websocket_urlpatterns = [
    path("ws/notifications/", NotificationConsumer.as_asgi()),
    path("ws/chat/<str:session_id>/", ChatConsumer.as_asgi()),
]

if os.getenv("DEBUG") == "True":
    from django.conf.urls.static import static

    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
