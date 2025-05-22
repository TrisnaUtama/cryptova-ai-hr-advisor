import json
import os
import uuid

from dotenv import load_dotenv
from openai import OpenAI
from agents import Agent, InputGuardrailTripwireTriggered, Tool, Runner, trace, ItemHelpers, RunConfig
import asyncio
import nest_asyncio
import ast
import markdown
from openai.types.responses import ResponseTextDeltaEvent, ResponseOutputMessage

load_dotenv()

API_KEY = os.environ.get("OPENAI_API_KEY")
client = OpenAI(api_key=API_KEY)


class PromptManager:
    def __init__(self, messages=[], model="gpt-4.1-mini"):
        self.messages = messages
        self.model = model

    def add_message(self, role, content):
        self.messages.append({"role": role, "content": content})

    def set_messages(self, messages):
        self.messages = messages

    def get_messages(self):
        return self.messages

    def generate(self):
        response = client.chat.completions.create(
            model=self.model, messages=self.messages
        )
        return response.choices[0].message.content

    def generate_structured(self, schema):
        response = client.beta.chat.completions.parse(
            model=self.model, messages=self.messages, response_format=schema
        )

        result = response.choices[0].message.model_dump()
        content = json.loads(result["content"])
        return content


class PromptManagerAgent:
    def __init__(
        self,
        messages: list = [],
        model: str = "gpt-4.1-mini-2025-04-14",
        tools: list = None,
        guardrail: list = None,
        agent_id: str = None,
        thread_id: str = None,
        last_result: list = [],
        user_id: int = None
    ):
        self.messages = messages
        self.model = model
        self.tools = tools or []
        self.guardrail = guardrail or []
        self.agent = None
        self.last_result = last_result
        self.thread_id = thread_id or str(uuid.uuid4())
        if agent_id:
            self.agent = Agent.load(agent_id)
        self.user_id = user_id

    def add_message(self, role: str, content: str):
        self.messages.append({"role": role, "content": content})

    def set_messages(self, messages: list):
        self.messages = messages

    def get_messages(self):
        return self.messages

    def add_tool(self, tool: Tool):
        self.tools.append(tool)

    def set_tools(self, tools: list):
        self.tools = tools
        
    def add_guardrail(self, guardrail):
        self.guardrail.append(guardrail)

    def set_guardrails(self, guardrail: list):
        self.guardrail = guardrail

    def create_agent(self, name: str, instructions: str):
        """Create a new agent with the specified name and instructions"""
        self.agent = Agent(
            name=name,
            instructions=instructions,
            model=self.model,
            tools=self.tools,
            input_guardrails=self.guardrail  # Pass guardrails directly to Agent
        )
        return self.agent

    async def generate(self):
        """Generate a response using the agent framework"""
        if not self.agent:
            raise ValueError("No agent created. Call create_agent() first.")
        
        result = await Runner.run(self.agent, self.messages[-1]["content"])
        return result.final_output

    async def generate_stream(self):
        """Generate a streaming response using the agent framework"""
        if not self.agent:
            raise ValueError("No agent created. Call create_agent() first.")

        # If we have a previous result, use it to maintain conversation context
        if self.last_result:
            if type(self.last_result) != list:
                conversation_input = ast.literal_eval(self.last_result)
            else:
                conversation_input = self.last_result
            conversation_input.append(self.messages[-1])
            result = Runner.run_streamed(
                self.agent,
                input=conversation_input,
                context={
                    "user_id": self.user_id
                },
            )
        else:
            # First turn in the conversation
            result = Runner.run_streamed(
                self.agent,
                input=self.messages[-1]["content"]
            )

        async for event in result.stream_events():
            if event.type == "raw_response_event" and isinstance(event.data, ResponseTextDeltaEvent):
                yield {
                    "type": "raw_response_event",
                    "data": event.data
                }
            elif event.type == "agent_updated_stream_event":
                yield {
                    "type": "agent_update",
                    "content": f"Agent updated: {event.new_agent.name}"
                }
            elif event.type == "run_item_stream_event":
                if event.item.type == "tool_call_item":
                    yield {
                        "type": "tool_call",
                        "content": "Tool was called"
                    }
                elif event.item.type == "tool_call_output_item":
                    yield {
                        "type": "tool_output",
                        "content": event.item.output
                    }
                elif event.item.type == "message_output_item":
                    print(event)
                    yield {
                        "type": "message",
                        "content": ItemHelpers.text_message_output(event.item),
                        "raw_item" : event.item.raw_item
                    }

    def generate_with_agent(self):
        """Generate a response using the agent framework with multi-turn conversation support"""
        if not self.agent:
            raise ValueError("No agent created. Call create_agent() first.")
        
        import asyncio
        import nest_asyncio
        
        # Apply nest_asyncio to allow nested event loops
        nest_asyncio.apply()
        
        # Create a new event loop
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            # Use trace to track conversation with thread_id
            with trace(workflow_name="Conversation", group_id=self.thread_id):
                # If we have a previous result, use it to maintain conversation context
                if self.last_result:
                    # Get the conversation history and add the new message
                    if type(self.last_result) != list:
                        conversation_input = ast.literal_eval(self.last_result)
                    else:
                        conversation_input = self.last_result
                    conversation_input.append(self.messages[-1])
                    response = loop.run_until_complete(
                        Runner.run(self.agent, conversation_input)
                    )
                else:
                    # First turn in the conversation
                    response = loop.run_until_complete(
                        Runner.run(self.agent, self.messages[-1]["content"])
                    )
                
                # Store the result for the next turn
                self.last_result = str(response.to_input_list())
                return response
        finally:
            # Clean up the event loop
            loop.close()

    def generate_structured(self, schema: dict):
        """Generate a structured response using the parse endpoint"""
        if not self.agent:
            raise ValueError("No agent created. Call create_agent() first.")
        return self.agent.run_structured(self.messages[-1]["content"], schema)
    
    def append_last_result(self, result: dict):
        self.last_result.append(result)

    def set_last_result(self, last_result: list):
        self.last_result = last_result

    def set_thread_id(self, thread_id: str):
        """Set a new thread ID"""
        self.thread_id = thread_id
        self.last_result = [] 
        
def convert_markdown_to_html(markdown_text):
    """Convert markdown text to HTML with code and table support"""
    extensions = [
        'fenced_code',  # For code blocks
        'tables',       # For tables
        'nl2br',        # Convert newlines to <br>
        'sane_lists'    # Better list handling
        'def_list'
    ]
    return markdown.markdown(markdown_text, extensions=extensions)