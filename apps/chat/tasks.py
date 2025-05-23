from agents import GuardrailFunctionOutput, InputGuardrailTripwireTriggered, Runner, input_guardrail
from huey.contrib.djhuey import task
from apps.chat.models import Chat, ChatSession
from django.contrib.auth import get_user_model
from apps.job.models import Job
from core.ai.prompt_manager import PromptManagerAgent, warning_msg, PromptManager
from core.ai.system_prompt import CV_ADVISOR, GUARDRAILS_AGENT_PROMPT, FOLLOWUP_ACTION_PROMPT
from core.ai.tools import get_list_of_cvs, get_cv_information, get_list_of_cv_match_with_job_description
from core.ai.structured_model import FollowupActionBase
from core.methods import send_chat_message
import os
import asyncio
from asgiref.sync import sync_to_async
import ast

# Define the guardrail function with @input_guardrail decorator
@input_guardrail
async def chat_guardrail(ctx, agent, input):
    # Initialize guardrail agent
    guardrail_agent = PromptManagerAgent()
    guardrail_agent.create_agent(
        name="Guardrail Assistant",
        instructions=GUARDRAILS_AGENT_PROMPT
    )
    
    guardrail_prompt = f"""
    Analyze this user input and determine if it's appropriate for a CV/Resume assistant:
    
    User Input: "{input}"
    
    Rules:
    - ALLOW: Questions about CVs, resumes, candidate profiles, job qualifications, skills, experience, education, candidate screening, job matching
    - REJECT: General knowledge, personal life, entertainment, history, unrelated topics
    
    Respond with exactly one word:
    - "ALLOW" if the question is appropriate
    - "REJECT" if the question should be blocked
    """
    
    # Use Runner.run instead of generate() method
    result = await Runner.run(guardrail_agent.agent, guardrail_prompt)
    
    # Check if the input should be rejected
    is_rejected = "REJECT" in str(result.final_output).upper()
    
    return GuardrailFunctionOutput(
        output_info=str(result.final_output),
        tripwire_triggered=is_rejected
    )


@task()
def process_chat(message, session_id, user_id):
    User = get_user_model()
    job = None
    cv_id_list = []
    
    async def get_user():
        return await sync_to_async(User.objects.get)(id=user_id)
    
    async def get_job(job_id):
        if job_id:
            return await sync_to_async(Job.objects.get)(id=job_id)
        return None
    
    async def get_or_create_session(user):
        if session_id:
            try:
                session = await sync_to_async(ChatSession.objects.get)(id=session_id, user=user)
                return session
            except ChatSession.DoesNotExist:
                return await sync_to_async(ChatSession.objects.create)(user=user)
        return await sync_to_async(ChatSession.objects.create)(user=user)
    
    async def get_messages(session):
        return await sync_to_async(lambda: Chat.objects.filter(session=session).order_by("created_at"))()
    
    async def create_chat(session, user, role, message):
        return await sync_to_async(Chat.objects.create)(
            session=session,
            user=user,
            role=role,
            message=message
        )
    
    async def save_session(session):
        await sync_to_async(session.save)()

    async def update_last_chat(last_chat):
        await sync_to_async(last_chat.save)()

    async def get_list_applicants(job):
        def process_applicants():
            list_applicants = job.jobapplication_set.all()
            list_id = []
            for applicant in list_applicants:
                list_id.append(applicant.cv.id)
            return list_id
            
        return await sync_to_async(process_applicants)()
    
    async def main(user_id, message):
        # Get user
        user = await get_user()
        session = await get_or_create_session(user)
        job_id = session.job_id
        job = await get_job(job_id)

        cv_id_list = await get_list_applicants(job)
        
        # Initialize agent
        agent = PromptManagerAgent(
            user_id=user_id,
            list_cv_id=cv_id_list
        )
        agent.create_agent(
            name="Cryptova CV Advisor",
            instructions=CV_ADVISOR,
        )
        agent.add_tool(get_list_of_cvs)
        agent.add_tool(get_cv_information)
        agent.add_tool(get_list_of_cv_match_with_job_description)
        
        # Add the guardrail to the agent - this passes the decorated function directly
        agent.add_guardrail(chat_guardrail)

        # Get or create session
        agent.set_thread_id(session.id)
        
        if session.last_result:
            agent.set_last_result(ast.literal_eval(session.last_result))
        else:
            agent.set_last_result([])

        # Get messages
        messages = await get_messages(session)

        # Check if messages exist and create system message if needed
        if not await sync_to_async(messages.exists)():
            await create_chat(
                session=session,
                user=user,
                role="system",
                message="Answer the user in a friendly and helpful manner with a bit long sentence.",
            )

        # Create user message
        await create_chat(
            session=session,
            user=user,
            role="user",
            message=message
        )

        agent.append_last_result({"role": "user", "content": message})
        agent.add_message(role="user", content=message)

        async def process_stream():
            try:
                last_chat = None
                tool_call_output = None  # Define outside the loop
                final_message = ""
                async for event in agent.generate_stream():
                    if event["type"] == "raw_response_event":
                        data = event["data"]
                        token = data.delta
                        await sync_to_async(send_chat_message)(session.id, token)
                    elif event["type"] == "message":
                        final_message = event["content"]
                        raw_item = event["raw_item"]

                        last_chat = await create_chat(
                            session=session,
                            user=user,
                            role="assistant",
                            message=final_message
                        )
                        agent.append_last_result(raw_item.model_dump())
                        session.last_result = agent.last_result
                        await save_session(session)
                        await sync_to_async(send_chat_message)(
                            session.id,
                            {"message": final_message, "done": True}
                        )
                    elif event["type"] == "tool_output":
                        content = event["content"]
                        tool_call_output = content
                
                pm = PromptManager()
                pm.add_message(role="system", content=FOLLOWUP_ACTION_PROMPT)
                pm.add_message(role="user", content=f"Conversation Response: {final_message} \n Candidate Data: {tool_call_output}")
                result = pm.generate_structured(FollowupActionBase)
                print(result.get("action"))
                if result.get("action") != 'null':
                    print(last_chat)
                    last_chat.followup_action = result
                    await update_last_chat(last_chat)
                    print("send followup action")
                    await sync_to_async(send_chat_message)(
                        session.id,
                        {"message": result, "done": True}
                    )

                print(result)
                # You can use tool_call_output here after the stream is complete
                if tool_call_output:
                    # Do something with the final tool_call_output
                    pass
                    
            except InputGuardrailTripwireTriggered:
                await create_chat(session, user, "assistant", warning_msg)
                await sync_to_async(send_chat_message)(session.id, warning_msg)

        await process_stream()

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        loop.run_until_complete(main(user_id=user_id, message=message))
    finally:
        loop.close()