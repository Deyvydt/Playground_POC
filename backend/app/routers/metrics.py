from datetime import datetime, timedelta
from fastapi import APIRouter, Depends
from sqlmodel import Session, select, func
from app.database import get_session
from app.models import MetricLog, Agent, Conversation

router = APIRouter(prefix="/api/metrics", tags=["metrics"])

# Precio aproximado de referencia de un modelo comercial en la nube (USD por 1K tokens)
# Se usa unicamente para ilustrar el ahorro de costos frente a modelos locales.
CLOUD_REFERENCE_PRICE_PER_1K = 0.03


@router.get("/summary")
def summary(session: Session = Depends(get_session)):
    logs = session.exec(select(MetricLog)).all()
    total_requests = len(logs)
    total_tokens = sum(l.total_tokens for l in logs)
    avg_latency = int(sum(l.latency_ms for l in logs) / total_requests) if total_requests else 0
    total_conversations = len(session.exec(select(Conversation)).all())
    total_agents = len(session.exec(select(Agent)).all())

    by_agent: dict[int, dict] = {}
    for log in logs:
        bucket = by_agent.setdefault(log.agent_id, {
            "agent_id": log.agent_id,
            "agent_name": log.agent_name,
            "requests": 0,
            "tokens": 0,
            "avg_latency_ms": 0,
            "_latency_sum": 0,
        })
        bucket["requests"] += 1
        bucket["tokens"] += log.total_tokens
        bucket["_latency_sum"] += log.latency_ms

    agents_breakdown = []
    for bucket in by_agent.values():
        bucket["avg_latency_ms"] = int(bucket["_latency_sum"] / bucket["requests"]) if bucket["requests"] else 0
        del bucket["_latency_sum"]
        agents_breakdown.append(bucket)

    estimated_cloud_cost = round((total_tokens / 1000) * CLOUD_REFERENCE_PRICE_PER_1K, 4)

    return {
        "total_requests": total_requests,
        "total_tokens": total_tokens,
        "avg_latency_ms": avg_latency,
        "total_conversations": total_conversations,
        "total_agents": total_agents,
        "local_cost_usd": 0.0,
        "estimated_cloud_cost_usd": estimated_cloud_cost,
        "agents_breakdown": agents_breakdown,
    }


@router.get("/timeseries")
def timeseries(session: Session = Depends(get_session)):
    logs = session.exec(select(MetricLog)).all()
    buckets: dict[str, dict] = {}
    now = datetime.utcnow()
    for i in range(6, -1, -1):
        day = (now - timedelta(days=i)).strftime("%Y-%m-%d")
        buckets[day] = {"date": day, "requests": 0, "tokens": 0}

    for log in logs:
        day = log.created_at.strftime("%Y-%m-%d")
        if day in buckets:
            buckets[day]["requests"] += 1
            buckets[day]["tokens"] += log.total_tokens

    return list(buckets.values())
