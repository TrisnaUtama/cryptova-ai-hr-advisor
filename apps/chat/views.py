import json
from django.http import JsonResponse
from django.shortcuts import render
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from apps.job.models import Job
from core.utils import LoginCheckMixin
from .models import ChatSession


class ChatHistoryView(LoginCheckMixin, View):
    def get(self, request):
        job_id = request.GET.get("job_id")
        if job_id:
            sessions = ChatSession.objects.filter(user=request.user, job_id=job_id)
        else:
            sessions = ChatSession.objects.filter(user=request.user)
        return render(request, "chat/index.html", {"sessions": sessions, "job_id": job_id})


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
        body = json.loads(request.body)
        job = Job.objects.get(id=body.get("job_id"))
        session = ChatSession.objects.create(user=request.user, job=job)
        return JsonResponse({"session_id": session.id})
    return JsonResponse({"error": "Unauthorized"}, status=401)
