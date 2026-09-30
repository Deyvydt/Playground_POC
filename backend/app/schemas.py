from datetime import datetime
from typing import Literal
from pydantic import BaseModel, Field

Role = Literal["admin", "developer", "viewer"]


class LoginRequest(BaseModel):
    email: str
    password: str


class UserCreate(BaseModel):
    name: str = Field(min_length=2)
    email: str = Field(min_length=3)
    title: str = ""
    role: Role = "viewer"
    password: str = Field(min_length=6)


class UserUpdate(BaseModel):
    name: str | None = None
    email: str | None = None
    title: str | None = None
    role: Role | None = None
    is_active: bool | None = None
    password: str | None = Field(default=None, min_length=6)


class AgentCreate(BaseModel):
    name: str = Field(min_length=2)
    icon: str = "bot"
    description: str = ""
    role_prompt: str = Field(min_length=5)
    model: str = "llama3.2:3b"
    temperature: float = Field(default=0.4, ge=0, le=1)
    tools: list[str] = []


class AgentUpdate(BaseModel):
    name: str | None = None
    icon: str | None = None
    description: str | None = None
    role_prompt: str | None = None
    model: str | None = None
    temperature: float | None = Field(default=None, ge=0, le=1)
    tools: list[str] | None = None
    status: Literal["active", "inactive"] | None = None


class AgentRead(BaseModel):
    id: int
    name: str
    icon: str
    description: str
    role_prompt: str
    model: str
    temperature: float
    tools: list[str]
    status: str
    created_by: str
    created_at: datetime


class ChatRequest(BaseModel):
    message: str = Field(min_length=1)
    conversation_id: int | None = None


class OrchestrationRequest(BaseModel):
    input_text: str = Field(min_length=1)
    pipeline: list[int] = Field(min_length=1)  # ids de agentes en orden
