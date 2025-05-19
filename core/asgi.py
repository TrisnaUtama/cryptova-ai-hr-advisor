"""
ASGI config for core project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.2/howto/deployment/asgi/
"""

import os

from channels.auth import AuthMiddlewareStack
from channels.routing import ProtocolTypeRouter, URLRouter
from django.core.asgi import get_asgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")

import django
from core.urls import websocket_urlpatterns

django.setup()

application = ProtocolTypeRouter(
    {
        "http": get_asgi_application(),
        # Add your WebSocket URL routing here
        "websocket": AuthMiddlewareStack(URLRouter(websocket_urlpatterns)),
    }
)
