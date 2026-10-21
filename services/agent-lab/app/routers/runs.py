import uuid
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from app.auth import Caller, get_caller
from app.graphs import agentfactory, talentia

router = APIRouter(prefix="/lab", tags=["runs"])


class RunIn(BaseModel):
    cv: str = ""
    vacante: str = ""
    requerimiento: str = ""


@router.post("/runs/{sistema}")
async def run(sistema: str, payload: RunIn, _: Caller = Depends(get_caller)):
    run_id = str(uuid.uuid4())
    if sistema == "talentia":
        if not payload.cv.strip() or not payload.vacante.strip():
            raise HTTPException(422, "Se requieren 'cv' y 'vacante'")
        estado_inicial = {"run_id": run_id, "cv": payload.cv, "vacante": payload.vacante, "trace": []}
        grafo = talentia.build_graph()
    elif sistema == "agentfactory":
        if not payload.requerimiento.strip():
            raise HTTPException(422, "Se requiere 'requerimiento'")
        estado_inicial = {
            "run_id": run_id,
            "requerimiento": payload.requerimiento,
            "ronda": 0,
            "observaciones": "",
            "trace": [],
        }
        grafo = agentfactory.build_graph()
    else:
        raise HTTPException(404, f"Sistema '{sistema}' no soportado")

    resultado = await grafo.ainvoke(estado_inicial)
    return {
        "run_id": run_id,
        "sistema": sistema,
        "error": resultado.get("error"),
        "trace": resultado.get("trace", []),
        "resultado": {k: v for k, v in resultado.items() if k not in ("trace", "run_id", "error")},
    }
