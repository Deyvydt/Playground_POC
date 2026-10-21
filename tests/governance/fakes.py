"""Doble de la API de administración de LiteLLM: keys, teams y registros de llamadas en memoria."""
import hashlib
import itertools
from datetime import datetime, timedelta

from app.litellm_admin import GatewayError


class FakeGateway:
    def __init__(self):
        self.reset()

    def reset(self):
        self.keys: dict[str, dict] = {}
        self.teams: dict[str, dict] = {}
        self.logs: dict[str, list[dict]] = {}
        self.down = False
        self._seq = itertools.count(1)

    def _check(self):
        if self.down:
            raise GatewayError("El gateway no está disponible")

    def _get(self, key_hash):
        self._check()
        if key_hash not in self.keys:
            raise GatewayError("El gateway rechazó la operación (404): key no encontrada")
        return self.keys[key_hash]

    async def is_available(self):
        return not self.down

    async def generate_key(self, **fields):
        self._check()
        key = f"sk-prueba-{next(self._seq):04d}"
        token = hashlib.sha256(key.encode()).hexdigest()
        self.keys[token] = {"key": key, "fields": dict(fields), "blocked": False, "spend": 0.0,
                            "last_active": None, "budget_reset_at": "2026-11-01T00:00:00+00:00"}
        return {"key": key, "token": token}

    async def update_key(self, key_hash, **fields):
        self._get(key_hash)["fields"].update(fields)
        return {"key": key_hash}

    async def delete_key(self, key_hash):
        self._get(key_hash)
        del self.keys[key_hash]

    async def block_key(self, key_hash):
        self._get(key_hash)["blocked"] = True

    async def unblock_key(self, key_hash):
        self._get(key_hash)["blocked"] = False

    async def key_info(self, key_hash):
        k = self._get(key_hash)
        return {"spend": k["spend"], "max_budget": k["fields"].get("max_budget"), "blocked": k["blocked"],
                "budget_reset_at": k["budget_reset_at"], "last_active": k["last_active"]}

    async def team_info(self, team_id):
        self._check()
        return self.teams.get(team_id, {"spend": 0.0, "max_budget": None})

    async def recent_logs(self, key_hash, minutes):
        self._check()
        return list(self.logs.get(key_hash, []))

    # --- utilidades para preparar escenarios ---
    def set_spend(self, key_hash, spend, max_budget=None):
        self.keys[key_hash]["spend"] = spend
        if max_budget is not None:
            self.keys[key_hash]["fields"]["max_budget"] = max_budget

    def add_logs(self, key_hash, total, failures):
        now = datetime.utcnow()
        self.logs[key_hash] = [
            {"startTime": (now - timedelta(seconds=i)).isoformat(), "endTime": (now - timedelta(seconds=i) + timedelta(milliseconds=250)).isoformat(),
             "status": "failure" if i < failures else "success", "model_group": "llama-local",
             "prompt_tokens": 10, "completion_tokens": 5, "spend": 0.001}
            for i in range(total)
        ]

    def hash_of(self, key):
        return hashlib.sha256(key.encode()).hexdigest()
