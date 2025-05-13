from django.shortcuts import render, redirect
from django.views import View
from core.utils import LoginCheckMixin
from .models import Chat, ChatSession
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator


class ChatHistoryView(LoginCheckMixin, View):
    def get(self, request):
        sessions = ChatSession.objects.filter(user=request.user)
        return render(request, "chat/index.html", {"sessions": sessions})


class ChatRoomView(LoginCheckMixin, View):
    @method_decorator(csrf_exempt)
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)

    def get(self, request):
        # Saat pertama buka, session_id kosong
        return render(
            request,
            "chat/room.html",
            {"chats": [], "show_greeting": True, "session_id": ""},
        )

    def post(self, request):
        message = request.POST.get("question")
        session_id = request.POST.get("session_id")
        chats = []
        session = None
        if message:
            if session_id:
                try:
                    session = ChatSession.objects.get(id=session_id, user=request.user)
                except ChatSession.DoesNotExist:
                    session = ChatSession.objects.create(user=request.user)
            else:
                session = ChatSession.objects.create(user=request.user)
            Chat.objects.create(
                session=session, user=request.user, role="user", message=message
            )
            Chat.objects.create(
                session=session,
                user=request.user,
                role="assistant",
                message="Hello! I'm CV-Insight-AI, your assistant for analyzing candidate CVs. How can I help you today?",
            )
            chats = list(session.chats.order_by("created_at"))
        return render(
            request,
            "chat/room.html",
            {
                "chats": chats,
                "show_greeting": False,
                "session_id": session.id if session else "",
            },
        )
