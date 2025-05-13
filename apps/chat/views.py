from django.shortcuts import render
from django.views import View
from core.utils import LoginCheckMixin
from .models import Chat
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator


class ChatHistoryView(LoginCheckMixin, View):
    def get(self, request):
        chats = Chat.objects.filter(user=request.user)
        return render(request, "chat/index.html", {"chats": chats})


class ChatRoomView(LoginCheckMixin, View):
    @method_decorator(csrf_exempt)
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)

    def get(self, request):
        return render(request, "chat/room.html", {"chats": [], "show_greeting": True})

    def post(self, request):
        question = request.POST.get("question")
        if question:
            chat = Chat.objects.create(
                user=request.user, role="user", question=question
            )
            # Simulasi jawaban AI, ganti dengan logic AI asli jika ada
            answer = "Hello! I'm CV-Insight-AI, your assistant for analyzing candidate CVs. How can I help you today?"
            chat.answer = answer
            chat.save()
        chats = Chat.objects.filter(user=request.user).order_by("created_at")
        return render(request, "chat/room.html", {"chats": chats})
