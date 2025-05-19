from huey.contrib.djhuey import task
from apps.chat.models import Chat, ChatSession
from django.contrib.auth import get_user_model
from core.ai.prompt_manager import PromptManagerAgent
from core.ai.system_prompt import CV_ADVISOR
from core.ai.tools import get_cv_by_job_category, get_list_of_highest_cv_score, get_cv_by_id
from core.methods import send_chat_message
from openai import OpenAI
import os
import asyncio
from openai.types.responses import ResponseTextDeltaEvent
from asgiref.sync import sync_to_async
import ast


@task()
def process_chat(message, session_id, user_id):
    User = get_user_model()
    user = User.objects.get(id=user_id)
    agent = PromptManagerAgent()
    agent.create_agent(
        name="Cryptova CV Advisor",
        instructions=CV_ADVISOR
    )
    agent.add_tool(get_cv_by_job_category)
    agent.add_tool(get_list_of_highest_cv_score)
    agent.add_tool(get_cv_by_id)


    # Check or create chat session
    session = None
    if session_id:
        try:
            session = ChatSession.objects.get(id=session_id, user=user)
            agent.set_thread_id(session.id)
            if session.last_result:
                agent.set_last_result(ast.literal_eval(session.last_result))
            else:
                agent.set_last_result([])
        except ChatSession.DoesNotExist:
            session = ChatSession.objects.create(user=user)
            agent.set_thread_id(session.id)
            agent.set_last_result([])
    else:
        session = ChatSession.objects.create(user=user)
        agent.set_thread_id(session.id)
        agent.set_last_result([])

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
    agent.append_last_result({"role": "user", "content": message})
    agent.add_message(role="user", content=message)

    async def process_stream():
        async for event in agent.generate_stream():
            if event["type"] == "raw_response_event":
                data = event["data"]
                token = data.delta
                await sync_to_async(send_chat_message)(session.id, token)
            elif event["type"] == "message":
                content = event["content"]
                raw_item = event["raw_item"]

                await sync_to_async(Chat.objects.create)(
                    session=session,
                    user=user,
                    role="assistant",
                    message=content
                )
                agent.append_last_result(raw_item.model_dump())
                session.last_result = agent.last_result
                await sync_to_async(session.save)()
                await sync_to_async(send_chat_message)(
                    session.id,
                    {"message": content, "done": True}
                )

    # Create new event loop and run the async function
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        loop.run_until_complete(process_stream())
    finally:
        loop.close()
