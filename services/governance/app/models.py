from datetime import datetime
from typing import Optional
from sqlmodel import JSON, Column, Field, SQLModel


class Organization(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    created_at: datetime = Field(default_factory=datetime.utcnow)


class Area(SQLModel, table=True):
    id: str = Field(primary_key=True)  # igual al team_id del gateway
    name: str
    organization_id: int = Field(foreign_key="organization.id")
    created_at: datetime = Field(default_factory=datetime.utcnow)


class Sistema(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    slug: str = Field(index=True, unique=True)
    name: str
    area_id: str = Field(foreign_key="area.id")
    description: str = ""
    owner_name: str = ""
    owner_email: str = ""
    created_at: datetime = Field(default_factory=datetime.utcnow)


class Agente(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    slug: str = Field(index=True)
    description: str = ""
    sistema_id: int = Field(foreign_key="sistema.id")
    area_id: str = Field(foreign_key="area.id")
    owner_name: str = ""
    owner_email: str = ""
    status: str = "activo"  # activo | pausado
    pause_reason: Optional[str] = None
    paused_by: Optional[str] = None  # nombre del admin o "automático"
    paused_at: Optional[datetime] = None
    runtime: str = "external"  # external | hosted (Opción 1)
    # Solo alias y hash: la key en claro se entrega una vez y no se guarda.
    key_alias: str = Field(index=True, unique=True)
    key_hash: str = Field(index=True)
    models: list[str] = Field(default_factory=list, sa_column=Column(JSON))
    max_budget: Optional[float] = None
    budget_duration: Optional[str] = None
    tpm_limit: Optional[int] = None
    rpm_limit: Optional[int] = None
    budget_warning_sent: bool = False
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = None


class Notification(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    kind: str  # registro | baja | regeneracion | pausa_manual | reactivacion | auto_pausa_gasto | auto_pausa_errores | aviso_gasto | alerta_gateway
    severity: str = "info"  # info | warning | critical
    title: str
    message: str = ""
    agente_id: Optional[int] = Field(default=None, foreign_key="agente.id")
    area_id: Optional[str] = None
    read: bool = False
    created_at: datetime = Field(default_factory=datetime.utcnow, index=True)
