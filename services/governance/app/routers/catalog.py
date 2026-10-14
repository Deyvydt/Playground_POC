import asyncio
from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, func, select
from app import litellm_admin, registry
from app.auth import Caller, get_caller, require_admin
from app.database import get_session
from app.models import Agente, Area, Organization, Sistema
from app.schemas import SistemaIn

router = APIRouter(prefix="/gov", tags=["catalog"])


@router.get("/health")
async def health():
    return {"status": "ok", "gateway_available": await litellm_admin.is_available()}


async def _team_usage(area_id: str) -> dict:
    try:
        info = await litellm_admin.team_info(area_id)
    except litellm_admin.GatewayError:
        return {"available": False}
    spend = float(info.get("spend") or 0)
    budget = info.get("max_budget")
    return {
        "available": True,
        "spend": spend,
        "max_budget": budget,
        "budget_ratio": (spend / budget) if budget else None,
        "tpm_limit": info.get("tpm_limit"),
        "rpm_limit": info.get("rpm_limit"),
    }


@router.get("/areas")
async def list_areas(session: Session = Depends(get_session), _: Caller = Depends(get_caller)):
    org = session.exec(select(Organization)).first()
    areas = session.exec(select(Area).order_by(Area.name)).all()
    usages = await asyncio.gather(*(_team_usage(a.id) for a in areas))
    result = []
    for area, usage in zip(areas, usages):
        agentes = session.exec(select(Agente).where(Agente.area_id == area.id)).all()
        result.append({
            "id": area.id,
            "name": area.name,
            "organization": org.name if org else None,
            "sistemas": session.exec(select(func.count()).select_from(Sistema).where(Sistema.area_id == area.id)).one(),
            "agentes": len(agentes),
            "agentes_pausados": sum(1 for a in agentes if a.status == "pausado"),
            "usage": usage,
        })
    return result


@router.get("/sistemas")
def list_sistemas(session: Session = Depends(get_session), _: Caller = Depends(get_caller)):
    sistemas = session.exec(select(Sistema).order_by(Sistema.name)).all()
    return [
        {
            **s.model_dump(),
            "area_name": session.get(Area, s.area_id).name,
            "agentes": session.exec(select(func.count()).select_from(Agente).where(Agente.sistema_id == s.id)).one(),
        }
        for s in sistemas
    ]


@router.post("/sistemas", status_code=201)
def create_sistema(payload: SistemaIn, session: Session = Depends(get_session), _: Caller = Depends(require_admin)):
    if not session.get(Area, payload.area_id):
        raise HTTPException(404, "Área no encontrada")
    slug = registry.slugify(payload.name)
    if session.exec(select(Sistema).where(Sistema.slug == slug)).first():
        raise HTTPException(409, f"Ya existe un sistema llamado '{payload.name}'")
    sistema = Sistema(slug=slug, **payload.model_dump())
    session.add(sistema)
    session.commit()
    session.refresh(sistema)
    return sistema
