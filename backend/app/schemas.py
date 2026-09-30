from datetime import datetime
from pydantic import BaseModel


class AgentCreate(BaseModel):
    name: str
    avatar_emoji: str = "🤖"
    description: str = ""
    role_prompt: str
    model: str = "llama3.2:3b"
    temperature: float = 0.4
    tools: list[str] = []


class AgentUpdate(BaseModel):
    name: str | None = None
    avatar_emoji: str | None = None
    description: str | None = None
    role_prompt: str | None = None
    model: str | None = None
    temperature: float | None = None
    tools: list[str] | None = None
    status: str | None = None


class AgentRead(BaseModel):
    id: int
    name: str
    avatar_emoji: str
    description: str
    role_prompt: str
    model: str
    temperature: float
    tools: list[str]
    status: str
    created_by: str
    created_at: datetime


class ChatRequest(BaseModel):
    message: str
    conversation_id: int | None = None


class ChatResponse(BaseModel):
    conversation_id: int
    message: dict
    trace: list[dict]
    latency_ms: int
    prompt_tokens: int
    completion_tokens: int


class OrchestrationRequest(BaseModel):
    input_text: str
    pipeline: list[int]  # ordered list of agent ids


class OrchestrationStep(BaseModel):
    agent_id: int
    agent_name: str
    avatar_emoji: str
    output: str
    trace: list[dict]
    latency_ms: int


class OrchestrationResponse(BaseModel):
    steps: list[OrchestrationStep]
    final_output: str
