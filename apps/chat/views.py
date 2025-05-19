from django.shortcuts import redirect, render
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.csrf import csrf_exempt

from core.utils import LoginCheckMixin

from .models import Chat, ChatSession
from core.ai.prompt_manager import PromptManagerAgent, convert_markdown_to_html


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
        agent = PromptManagerAgent()
        agent.create_agent(
            name="CV-Insight-AI",
            instructions="You are a helpful assistant that can answer questions about candidate CVs.",
        )
        if message:
            if session_id:
                try:
                    session = ChatSession.objects.get(id=session_id, user=request.user)
                    agent.set_thread_id(session.id)
                    agent.set_last_result(session.last_result)
                except ChatSession.DoesNotExist:
                    session = ChatSession.objects.create(user=request.user)
                    is_new_session = True
                    agent.set_thread_id(session.id)
                    
            else:
                session = ChatSession.objects.create(user=request.user)
                is_new_session = True
                agent.set_thread_id(session.id)
            
            agent.add_message(
                role="user",
                content=message
            )

            Chat.objects.create(
                session=session, user=request.user, role="user", message=message
            )
            response = agent.generate_with_agent()

            # Convert markdown response to HTML
            html_response = convert_markdown_to_html(response.final_output)

            Chat.objects.create(
                session=session, user=request.user, role="assistant", message=html_response
            )
            
            session.last_result = response.to_input_list()
            session.save()
            
            if is_new_session:
                return redirect(f"/chat?session_id={session.id}")
            
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