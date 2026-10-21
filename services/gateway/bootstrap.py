"""Crea o actualiza los teams (áreas) del gateway. Se puede ejecutar varias veces.

Uso: python bootstrap.py
"""
from admin import client

TEAMS = [
    {
        "team_id": "rrhh",
        "team_alias": "RR.HH. (Talentia)",
        "models": ["local-models"],
        "max_budget": 5.0,
        "budget_duration": "30d",
        "tpm_limit": 20000,
        "rpm_limit": 60,
    },
    {
        "team_id": "desarrollo",
        "team_alias": "Desarrollo (AgentFactory)",
        "models": ["local-models"],
        "max_budget": 5.0,
        "budget_duration": "30d",
        "tpm_limit": 30000,
        "rpm_limit": 60,
    },
    {
        "team_id": "plataforma",
        "team_alias": "Plataforma (TokenIO)",
        "models": ["local-models"],
        "max_budget": 5.0,
        "budget_duration": "30d",
        "tpm_limit": 30000,
        "rpm_limit": 120,
    },
]


def main() -> None:
    with client() as c:
        for team in TEAMS:
            exists = c.get("/team/info", params={"team_id": team["team_id"]}).status_code == 200
            r = c.post("/team/update" if exists else "/team/new", json=team)
            r.raise_for_status()
            print(f"{'actualizado' if exists else 'creado':>11}  {team['team_id']:<11} {team['team_alias']}")


if __name__ == "__main__":
    main()
