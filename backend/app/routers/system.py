from fastapi import APIRouter
from app import ollama_client
from app.tools import TOOL_DEFINITIONS

router = APIRouter(prefix="/api", tags=["system"])


@router.get("/health")
async def health():
    ollama_up = await ollama_client.is_available()
    return {"status": "ok", "ollama_available": ollama_up}


@router.get("/models")
async def models():
    raw = await ollama_client.list_models()
    return [{"name": m.get("name"), "size": m.get("size")} for m in raw]


@router.get("/tools")
def tools_catalog():
    return [
        {"name": t["function"]["name"], "description": t["function"]["description"]}
        for t in TOOL_DEFINITIONS
    ]
