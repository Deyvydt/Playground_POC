import asyncio
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlmodel import Session
from app import monitor
from app.config import CORS_ORIGIN
from app.database import engine, init_db
from app.routers import agents, alerts, catalog, notifications
from app.seed import run_seed

logging.basicConfig(level=logging.INFO)


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    with Session(engine) as session:
        run_seed(session)
    task = asyncio.create_task(monitor.loop())
    yield
    task.cancel()


app = FastAPI(title="TokenIO Governance", version="0.1.0", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[CORS_ORIGIN],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(catalog.router)
app.include_router(agents.router)
app.include_router(notifications.router)
app.include_router(alerts.router)
