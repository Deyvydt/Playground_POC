import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database import init_db
from app.config import CORS_ORIGIN
from app.seed import run_seed, seed_sample_knowledge
from app.routers import agents, auth, knowledge, chat, orchestration, metrics, users, system

logging.basicConfig(level=logging.INFO)


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    run_seed()
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
