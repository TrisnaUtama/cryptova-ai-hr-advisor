import json
import os
import uuid

from dotenv import load_dotenv
from openai import OpenAI
from pydantic import BaseModel, Field
from agents import Agent, Tool, Runner, trace
import asyncio
import nest_asyncio
import ast
import markdown
from markdown.extensions import fenced_code, tables

load_dotenv()

API_KEY = os.environ.get("OPENAI_API_KEY")
client = OpenAI(api_key=API_KEY)


class PromptManager:
    def __init__(self, messages=[], model="gpt-4.1-mini-2025-04-14"):
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


class EducationsBase(BaseModel):
    degree: str = Field(description="The degree of the candidate")
    year: str = Field(description="The year of the candidate")
    institution: str = Field(description="The institution of the candidate")
    gpa: str = Field(description="The GPA of the candidate")


class WorkExperienceBase(BaseModel):
    position: str = Field(
        description="The position of the work experience of the candidate"
    )
    company: str = Field(
        description="The company of the work experience of the candidate"
    )
    duration: str = Field(
        description="The duration of the work experience of the candidate"
    )
    description: str = Field(
        description="The description of the work experience of the candidate"
    )


class SkillBase(BaseModel):
    skill: str = Field(description="The skill of the candidate")
    proficiency: str = Field(description="The proficiency of the candidate")


class LanguageBase(BaseModel):
    language: str = Field(description="The language of the candidate")
    proficiency: str = Field(description="The proficiency of the candidate")


class AchievementBase(BaseModel):
    title: str = Field(description="The title of the achievement")
    description: str = Field(description="The description of the achievement")
    year: str = Field(description="The year of the achievement")
    publisher: str = Field(description="The publisher of the achievement")


class CVBase(BaseModel):
    raw_output: str
    candidate_name: str = Field(description="The name of the candidate")
    candidate_email: str = Field(description="The email of the candidate")
    candidate_phone: str = Field(description="The phone number of the candidate")
    candidate_title: str = Field(description="The job title of the candidate")
    description: str = Field(description="The description of the candidate")
    education: list[EducationsBase] = Field(
        description="The education of the candidate"
    )
    workexperience: list[WorkExperienceBase] = Field(
        description="The work experience of the candidate"
    )
    skills: list[SkillBase] = Field(description="The skills of the candidate")
    language: list[LanguageBase] = Field(description="The language of the candidate")
    achievements: list[AchievementBase] = Field(
        description="The achievements of the candidate"
    )
    overall_score: float = Field(description="The overall score of the candidate")
    experience_score: float = Field(description="The experience score of the candidate")
    achievement_score: float = Field(
        description="The achievement score of the candidate"
    )
    skill_score: float = Field(description="The skill score of the candidate")


class PromptManagerAgent:
    def __init__(
        self,
        messages: list = [],
        model: str = "gpt-4.1-mini-2025-04-14",
        tools: list = None,
        agent_id: str = None,
        thread_id: str = None
    ):
        self.messages = messages
        self.model = model
        self.tools = tools or []
        self.agent = None
        self.last_result = None
        self.thread_id = thread_id or str(uuid.uuid4())  # Generate new thread_id if not provided
        if agent_id:
            self.agent = Agent.load(agent_id)

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

    def create_agent(self, name: str, instructions: str):
        """Create a new agent with the specified name and instructions"""
        self.agent = Agent(
            name=name,
            instructions=instructions,
            model=self.model,
            tools=self.tools
        )
        return self.agent

    def generate(self):
        """Generate a response using the standard chat completion"""
        if not self.agent:
            raise ValueError("No agent created. Call create_agent() first.")
        return self.agent.chat(self.messages[-1]["content"])

    def generate_with_agent(self):
        """Generate a response using the agent framework with multi-turn conversation support"""
        if not self.agent:
            raise ValueError("No agent created. Call create_agent() first.")
        
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
                    print(self.last_result)
                    # Get the conversation history and add the new message
                    conversation_input = ast.literal_eval(self.last_result)
                    print(conversation_input)
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
                print(response)
                return response
        finally:
            # Clean up the event loop
            loop.close()

    def generate_structured(self, schema: dict):
        """Generate a structured response using the parse endpoint"""
        if not self.agent:
            raise ValueError("No agent created. Call create_agent() first.")
        return self.agent.run_structured(self.messages[-1]["content"], schema)

    def set_last_result(self, last_result: list):
        self.last_result = last_result

    def set_thread_id(self, thread_id: str):
        """Set a new thread ID"""
        self.thread_id = thread_id
        self.last_result = None  # Reset conversation state when changing threads

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