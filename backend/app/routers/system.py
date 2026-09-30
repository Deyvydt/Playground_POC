from fastapi import APIRouter, Depends
from app import ollama_client
from app.config import EMBED_MODEL
from app.models import User
from app.security import PERMISSIONS, get_current_user
from app.tools import TOOL_DEFINITIONS

router = APIRouter(prefix="/api", tags=["system"])


@router.get("/health")
async def health():
    ollama_up = await ollama_client.is_available()
    return {"status": "ok", "ollama_available": ollama_up}


@router.get("/models")
async def models(_: User = Depends(get_current_user)):
    raw = await ollama_client.list_models()
    return [
        {
            "name": m.get("name"),
            "size": m.get("size"),
            "family": (m.get("details") or {}).get("family"),
            "parameters": (m.get("details") or {}).get("parameter_size"),
            "embedding": m.get("name", "").split(":")[0] == EMBED_MODEL,
        }
        for m in raw
    ]


@router.get("/tools")
def tools_catalog(_: User = Depends(get_current_user)):
    return [
        {"name": t["function"]["name"], "description": t["function"]["description"]}
        for t in TOOL_DEFINITIONS
    ]


@router.get("/roles")
def roles(_: User = Depends(get_current_user)):
    return {role: sorted(perms) for role, perms in PERMISSIONS.items()}
