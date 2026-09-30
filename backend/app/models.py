from datetime import datetime
from typing import Optional
from sqlmodel import SQLModel, Field, Column, JSON


class User(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    email: str = Field(default="", index=True)
    password_hash: str = ""
    role: str  # admin | developer | viewer
    title: str = ""
    is_active: bool = True
    avatar_emoji: str = ""  # legado, ya no se usa en la interfaz
    created_at: Optional[datetime] = Field(default_factory=datetime.utcnow)
    last_login_at: Optional[datetime] = None


class Agent(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    icon: str = "bot"
    avatar_emoji: str = ""  # legado, ya no se usa en la interfaz
    description: str = ""
    role_prompt: str
    model: str = "llama3.2:3b"
    temperature: float = 0.4
    tools: list[str] = Field(default_factory=list, sa_column=Column(JSON))
    status: str = "active"  # active | inactive
    created_by: str = "Admin"
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = None


class KnowledgeDocument(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    agent_id: int = Field(foreign_key="agent.id")
    filename: str
    chunk_count: int = 0
    uploaded_at: datetime = Field(default_factory=datetime.utcnow)


class KnowledgeChunk(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    document_id: int = Field(foreign_key="knowledgedocument.id")
    agent_id: int = Field(foreign_key="agent.id")
    chunk_index: int
    content: str
    embedding: list[float] = Field(default_factory=list, sa_column=Column(JSON))


class Conversation(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    agent_id: int = Field(foreign_key="agent.id")
    user_id: Optional[int] = None
    title: str = "Nueva conversación"
    started_at: datetime = Field(default_factory=datetime.utcnow)


class Message(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    conversation_id: int = Field(foreign_key="conversation.id")
    role: str  # user | assistant
    content: str
    trace: list[dict] = Field(default_factory=list, sa_column=Column(JSON))
    latency_ms: int = 0
    prompt_tokens: int = 0
    completion_tokens: int = 0
    created_at: datetime = Field(default_factory=datetime.utcnow)


class MetricLog(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    agent_id: int = Field(foreign_key="agent.id")
    agent_name: str = ""
    user_id: Optional[int] = None
    model: str = ""
    latency_ms: int = 0
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    tool_calls: int = 0
    success: bool = True
    error_message: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
