import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlmodel import Session

from app import gateway_keys
from app.database import engine, init_db
from app.config import CORS_ORIGIN
from app.seed import run_seed, seed_sample_knowledge
from app.routers import agents, auth, knowledge, chat, orchestration, metrics, users, system

logging.basicConfig(level=logging.INFO)


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    run_seed()
    with Session(engine) as session:
        await gateway_keys.register_missing(session)
    await seed_sample_knowledge()
    yield


app = FastAPI(title="TCS Agent Playground API", version="1.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[CORS_ORIGIN, "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.exception_handler(OverflowError)
async def id_out_of_range(request: Request, exc: OverflowError):
    # Un id mayor que el entero de 64 bits de SQLite no puede existir: es un 404, no un error del servidor.
    if "SQLite INTEGER" in str(exc):
        return JSONResponse(status_code=404, content={"detail": "Recurso no encontrado"})
    raise exc


app.include_router(system.router)
app.include_router(auth.router)
app.include_router(agents.router)
app.include_router(knowledge.router)
app.include_router(chat.router)
app.include_router(orchestration.router)
app.include_router(metrics.router)
app.include_router(users.router)


@app.get("/")
def root():
    return {"name": "TCS Agent Playground API", "status": "running"}
