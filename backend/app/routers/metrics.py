from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, Query
from sqlmodel import Session, select
from app.database import get_session
from app.models import Agent, Conversation, MetricLog, User
from app.security import get_current_user, require

router = APIRouter(prefix="/api/metrics", tags=["metrics"])

# Precio de referencia de un modelo comercial en la nube (USD por 1K tokens), solo para
# estimar cuanto costaria el mismo consumo fuera de la infraestructura propia.
CLOUD_REFERENCE_PRICE_PER_1K = 0.03


def _cloud_cost(tokens: int) -> float:
    return round((tokens / 1000) * CLOUD_REFERENCE_PRICE_PER_1K, 4)


def _logs_since(session: Session, days: int) -> list[MetricLog]:
    since = datetime.utcnow() - timedelta(days=days)
    return session.exec(select(MetricLog).where(MetricLog.created_at >= since)).all()


def _group(logs: list[MetricLog], key, label) -> list[dict]:
    buckets: dict = {}
    for log in logs:
        k = key(log)
        b = buckets.setdefault(k, {
            "key": k, "name": label(log), "requests": 0, "errors": 0, "prompt_tokens": 0,
            "completion_tokens": 0, "tokens": 0, "tool_calls": 0, "_latency": 0,
        })
        b["requests"] += 1
        b["errors"] += 0 if log.success else 1
        b["prompt_tokens"] += log.prompt_tokens
        b["completion_tokens"] += log.completion_tokens
        b["tokens"] += log.total_tokens
        b["tool_calls"] += log.tool_calls
        b["_latency"] += log.latency_ms
    rows = []
    for b in buckets.values():
        b["avg_latency_ms"] = int(b.pop("_latency") / b["requests"]) if b["requests"] else 0
        b["cloud_cost_usd"] = _cloud_cost(b["tokens"])
        rows.append(b)
    return sorted(rows, key=lambda r: r["tokens"], reverse=True)


@router.get("/summary")
def summary(
    days: int = Query(30, ge=1, le=365),
    session: Session = Depends(get_session),
    _: User = Depends(get_current_user),
):
    logs = _logs_since(session, days)
    total_requests = len(logs)
    total_tokens = sum(l.total_tokens for l in logs)
    errors = sum(0 if l.success else 1 for l in logs)
    agents = session.exec(select(Agent)).all()
    users = {u.id: u.name for u in session.exec(select(User)).all()}

    by_agent = _group(logs, lambda l: l.agent_id, lambda l: l.agent_name)
    for row in by_agent:
        row["agent_id"] = row["key"]
        row["agent_name"] = row["name"]

    return {
        "days": days,
        "total_requests": total_requests,
        "total_tokens": total_tokens,
        "prompt_tokens": sum(l.prompt_tokens for l in logs),
        "completion_tokens": sum(l.completion_tokens for l in logs),
        "avg_latency_ms": int(sum(l.latency_ms for l in logs) / total_requests) if total_requests else 0,
        "error_rate": round(errors / total_requests, 4) if total_requests else 0,
        "tool_calls": sum(l.tool_calls for l in logs),
        "total_conversations": len(session.exec(select(Conversation)).all()),
        "total_agents": len(agents),
        "active_agents": sum(1 for a in agents if a.status == "active"),
        "local_cost_usd": 0.0,
        "estimated_cloud_cost_usd": _cloud_cost(total_tokens),
        "cloud_price_per_1k": CLOUD_REFERENCE_PRICE_PER_1K,
        "agents_breakdown": by_agent,
        "models_breakdown": _group(logs, lambda l: l.model, lambda l: l.model),
        "users_breakdown": _group(
            [l for l in logs if l.user_id], lambda l: l.user_id, lambda l: users.get(l.user_id, "Usuario eliminado")
        ),
    }


@router.get("/timeseries")
def timeseries(
    days: int = Query(14, ge=1, le=365),
    agent_id: int | None = None,
    session: Session = Depends(get_session),
    _: User = Depends(get_current_user),
):
    logs = _logs_since(session, days)
    if agent_id:
        logs = [l for l in logs if l.agent_id == agent_id]
    buckets: dict[str, dict] = {}
    now = datetime.utcnow()
    for i in range(days - 1, -1, -1):
        day = (now - timedelta(days=i)).strftime("%Y-%m-%d")
        buckets[day] = {"date": day, "requests": 0, "tokens": 0, "prompt_tokens": 0, "completion_tokens": 0, "errors": 0}

    for log in logs:
        day = log.created_at.strftime("%Y-%m-%d")
        if day in buckets:
            b = buckets[day]
            b["requests"] += 1
            b["tokens"] += log.total_tokens
            b["prompt_tokens"] += log.prompt_tokens
            b["completion_tokens"] += log.completion_tokens
            b["errors"] += 0 if log.success else 1

    return list(buckets.values())


@router.get("/activity")
def activity(
    limit: int = Query(8, ge=1, le=50),
    session: Session = Depends(get_session),
    _: User = Depends(require("metrics")),
):
    logs = session.exec(select(MetricLog).order_by(MetricLog.created_at.desc()).limit(limit)).all()
    users = {u.id: u.name for u in session.exec(select(User)).all()}
    return [
        {
            "id": l.id,
            "agent_id": l.agent_id,
            "agent_name": l.agent_name,
            "user_name": users.get(l.user_id) if l.user_id else None,
            "model": l.model,
            "tokens": l.total_tokens,
            "latency_ms": l.latency_ms,
            "success": l.success,
            "created_at": l.created_at,
        }
        for l in logs
    ]
