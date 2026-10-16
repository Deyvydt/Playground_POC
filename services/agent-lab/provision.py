"""Registra en governance los 8 agentes (nodos) de prueba de agent-lab y guarda sus keys cifradas.

Uso: python provision.py
Idempotente: si el nodo ya tiene una credencial guardada en la base de agent-lab, se omite.
"""
import httpx
from app import secrets
from app.config import GOVERNANCE_URL, SERVICE_TOKEN
from app.database import init_db

NODOS = {
    "talentia": ["analizador_cv", "evaluador_ajuste", "generador_entrevista", "redactor_comunicaciones"],
    "agentfactory": ["generador_codigo", "revisor_codigo", "generador_tests", "documentador"],
}

HEADERS = {"X-Service-Token": SERVICE_TOKEN, "X-Service-Name": "agent-lab"}


def _sistema_id(client: httpx.Client, slug: str) -> int:
    r = client.get("/gov/sistemas", headers=HEADERS)
    r.raise_for_status()
    for sistema in r.json():
        if sistema["slug"] == slug:
            return sistema["id"]
    raise RuntimeError(f"Sistema '{slug}' no existe en governance (¿corrió su seed?).")


def main() -> None:
    init_db()
    with httpx.Client(base_url=GOVERNANCE_URL, timeout=30) as client:
        for sistema, nodos in NODOS.items():
            sistema_id = _sistema_id(client, sistema)
            for nodo in nodos:
                if secrets.exists(sistema, nodo):
                    print(f"   omitido  {sistema}/{nodo} (ya registrado)")
                    continue
                payload = {
                    "name": f"{sistema} · {nodo}",
                    "sistema_id": sistema_id,
                    "description": f"Nodo de prueba ({nodo}) del grafo LangGraph de {sistema}.",
                    "runtime": "hosted",
                    "models": ["local-models"],
                }
                r = client.post("/gov/agents", json=payload, headers=HEADERS)
                r.raise_for_status()
                data = r.json()
                agente_id = data["agent"]["id"]
                key_alias = data["agent"]["key_alias"]
                key = data["connection"]["api_key"]
                secrets.save(sistema, nodo, agente_id, key_alias, key)
                print(f" registrado  {sistema}/{nodo} -> agente #{agente_id}")


if __name__ == "__main__":
    main()
