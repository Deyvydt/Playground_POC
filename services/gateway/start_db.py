"""Postgres local para los servicios de gobierno, sin Docker ni permisos de admin.

Uso: python start_db.py [start|stop|status]
"""
import os
import sys
from pathlib import Path

import pgserver

PGDATA = Path(__file__).resolve().parent.parent / ".data" / "pg"
HOST = "127.0.0.1"
PORT = int(os.getenv("PG_PORT", "5433"))
DATABASES = ["litellm", "governance"]


def psql(sql: str, database: str = "postgres") -> str:
    return pgserver.psql(["-h", HOST, "-p", str(PORT), "-U", "postgres", "-d", database, "-tAc", sql])


def is_running() -> bool:
    try:
        pgserver.pg_ctl(["status"], pgdata=PGDATA)
        return True
    except Exception:
        return False


def start() -> None:
    if not (PGDATA / "PG_VERSION").exists():
        PGDATA.mkdir(parents=True, exist_ok=True)
        pgserver.initdb(["-U", "postgres", "--auth=trust", "-E", "UTF8"], pgdata=PGDATA)
    if not is_running():
        # pgserver elige un puerto al azar; aquí se fija para que DATABASE_URL sea estable.
        pgserver.pg_ctl(
            ["-w", "-o", f'-h "{HOST}"', "-o", f"-p {PORT}", "-l", str(PGDATA / "server.log"), "start"],
            pgdata=PGDATA,
            timeout=30,
        )
    existing = set(psql("SELECT datname FROM pg_database").split())
    for name in DATABASES:
        if name not in existing:
            psql(f'CREATE DATABASE "{name}"')
    print(f"Postgres listo en postgresql://postgres@{HOST}:{PORT}  (bases: {', '.join(DATABASES)})")


def stop() -> None:
    if is_running():
        pgserver.pg_ctl(["-w", "stop"], pgdata=PGDATA, timeout=30)
    print("Postgres detenido")


if __name__ == "__main__":
    action = sys.argv[1] if len(sys.argv) > 1 else "start"
    {"start": start, "stop": stop, "status": lambda: print("activo" if is_running() else "detenido")}[action]()
