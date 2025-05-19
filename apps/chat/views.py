from django.http import JsonResponse
from django.shortcuts import render
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from core.utils import LoginCheckMixin
from .models import ChatSession


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
        if session_id:
            try:
                session = ChatSession.objects.get(id=session_id, user=request.user)
                chats = list(session.chats.order_by("created_at"))
            except ChatSession.DoesNotExist:
                session = None
        else:
            session = None
        return render(
            request,
            "chat/room.html",
            {
                "chats": chats,
                "session_id": session_id or "",
            },
        )


@csrf_exempt
def create_chat_session(request):
    if request.method == "POST" and request.user.is_authenticated:
        session = ChatSession.objects.create(user=request.user)
        return JsonResponse({"session_id": session.id})
    return JsonResponse({"error": "Unauthorized"}, status=401)
