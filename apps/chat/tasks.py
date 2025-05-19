from huey.contrib.djhuey import task
from apps.chat.models import Chat, ChatSession
from django.contrib.auth import get_user_model
from core.methods import send_chat_message
from openai import OpenAI
import os


@task()
def process_chat(message, session_id, user_id):
    User = get_user_model()
    user = User.objects.get(id=user_id)

    # Check or create chat session
    session = None
    if session_id:
        try:
            session = ChatSession.objects.get(id=session_id, user=user)
        except ChatSession.DoesNotExist:
            session = ChatSession.objects.create(user=user)
    else:
        session = ChatSession.objects.create(user=user)

    # Get user message
    messages = Chat.objects.filter(session=session).order_by("created_at")

    # Check if the message queryset is empty
    if not messages.exists():
        Chat.objects.create(
            session=session,
            user=user,
            role="system",
            message="Answer the user in a friendly and helpful manner with a bit long sentence.",
        )

    # Append user message to chat history
    Chat.objects.create(session=session, user=user, role="user", message=message)

    # Reterieve chat history
    messages = Chat.objects.filter(session=session).order_by("created_at")

    # Get chat history and map to OpenAI format
    messages = Chat.objects.filter(session=session).order_by("created_at")
    openai_messages = [
        {"role": str(m.role or "user"), "content": str(m.message)} for m in messages
    ]

    client = OpenAI(
        api_key=os.environ.get(
            "OPENAI_API_KEY", "<your OpenAI API key if not set as env var>"
        )
    )
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=openai_messages, # type: ignore
        stream=True
    )

    assistant_full = ""
    for chunk in response:
        content = chunk.choices[0].delta.content or ""
        assistant_full += content
        is_last = chunk.choices[0].finish_reason is not None
        send_chat_message(
            session.id,
            assistant_full
            if not is_last
            else {"message": assistant_full, "done": True},
        )

    # Save full assistant message
    Chat.objects.create(
        session=session,
        user=user,
        role="assistant",
        message=assistant_full,
    )
