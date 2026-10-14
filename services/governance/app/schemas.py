from typing import Optional
from pydantic import BaseModel, Field


class SistemaIn(BaseModel):
    name: str = Field(min_length=2, max_length=80)
    area_id: str
    description: str = ""
    owner_name: str = ""
    owner_email: str = ""


class AgentIn(BaseModel):
    name: str = Field(min_length=2, max_length=80)
    sistema_id: int
    description: str = ""
    owner_name: str = ""
    owner_email: str = ""
    runtime: str = Field(default="external", pattern="^(external|hosted)$")
    models: list[str] = Field(default_factory=lambda: ["local-models"], min_length=1)
    max_budget: Optional[float] = Field(default=1.0, ge=0)
    budget_duration: Optional[str] = "30d"
    tpm_limit: Optional[int] = Field(default=None, ge=1)
    rpm_limit: Optional[int] = Field(default=None, ge=1)


class AgentLimitsIn(BaseModel):
    models: Optional[list[str]] = None
    max_budget: Optional[float] = Field(default=None, ge=0)
    budget_duration: Optional[str] = None
    tpm_limit: Optional[int] = Field(default=None, ge=1)
    rpm_limit: Optional[int] = Field(default=None, ge=1)
    owner_name: Optional[str] = None
    owner_email: Optional[str] = None
    description: Optional[str] = None


class PauseIn(BaseModel):
    reason: str = Field(default="Pausa manual", max_length=300)
