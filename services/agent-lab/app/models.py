from datetime import datetime
from typing import Optional
from sqlmodel import Field, SQLModel


class AgentCredential(SQLModel, table=True):
    """Virtual key cifrada de un nodo (= un agente registrado en governance)."""

    id: Optional[int] = Field(default=None, primary_key=True)
    sistema: str = Field(index=True)
    nodo: str = Field(index=True)
    agente_id: int
    key_alias: str = Field(index=True, unique=True)
    key_enc: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
