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
        session_id = request.GET.get("session_id")
        chats = []
        show_greeting = True
        if session_id:
            try:
                session = ChatSession.objects.get(id=session_id, user=request.user)
                chats = list(session.chats.order_by("created_at"))
                show_greeting = False
            except ChatSession.DoesNotExist:
                session = None
        else:
            session = None
        return render(
            request,
            "chat/room.html",
            {
                "chats": chats,
                "show_greeting": show_greeting,
                "session_id": session_id or "",
            },
        )

    def post(self, request):
        message = request.POST.get("question")
        session_id = request.POST.get("session_id")
        chats = []
        session = None
        is_new_session = False
        if message:
            if session_id:
                try:
                    session = ChatSession.objects.get(id=session_id, user=request.user)
                except ChatSession.DoesNotExist:
                    session = ChatSession.objects.create(user=request.user)
                    is_new_session = True
            else:
                session = ChatSession.objects.create(user=request.user)
                is_new_session = True
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
            if is_new_session:
                return redirect(f"/chat?session_id={session.id}")
        return render(
            request,
            "chat/room.html",
            {
                "chats": chats,
                "show_greeting": False,
                "session_id": session.id if session else "",
            },
        )
