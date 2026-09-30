import logging
import random
from datetime import datetime, timedelta
from sqlmodel import Session, select
from app.config import SEED_DEMO_ACTIVITY
from app.database import engine
from app.models import User, Agent, MetricLog, KnowledgeDocument
from app.security import hash_password
from app import rag, ollama_client

logger = logging.getLogger("seed")

DEMO_PASSWORD = "Tcs2026!"

DEMO_USERS = [
    {"name": "Ana Ríos", "email": "ana.rios@tcs.com", "role": "admin", "title": "Gerente Regional"},
    {"name": "Carlos Vega", "email": "carlos.vega@tcs.com", "role": "developer", "title": "AI Engineer"},
    {"name": "Lucía Soto", "email": "lucia.soto@tcs.com", "role": "viewer", "title": "Analista de Negocio"},
]

DEMO_AGENTS = [
    {
        "name": "Soporte TI",
        "icon": "wrench",
        "description": "Resuelve incidencias y consulta tickets del Service Desk interno.",
        "role_prompt": (
            "Eres un agente de soporte de TI de TCS. Responde en español de forma clara y profesional. "
            "Si el usuario menciona un identificador de ticket, usa la herramienta consultar_ticket_interno. "
            "Si necesitas la fecha u hora, usa la herramienta fecha_actual."
        ),
        "model": "llama3.2:3b",
        "temperature": 0.3,
        "tools": ["consultar_ticket_interno", "fecha_actual"],
    },
    {
        "name": "Analista de Datos",
        "icon": "chart-column",
        "description": "Analiza cifras de negocio y realiza cálculos rápidos.",
        "role_prompt": (
            "Eres un analista de datos senior de TCS. Analizas la información entregada por el usuario, "
            "identificas tendencias clave y, cuando haga falta hacer una cuenta, usas la herramienta calculadora. "
            "Responde en español con un tono ejecutivo y estructurado (usa bullets cuando ayude)."
        ),
        "model": "llama3.2:3b",
        "temperature": 0.4,
        "tools": ["calculadora"],
    },
    {
        "name": "Redactor de Reportes",
        "icon": "file-text",
        "description": "Convierte análisis técnicos en reportes ejecutivos listos para presentar.",
        "role_prompt": (
            "Eres un redactor ejecutivo de TCS. Tomas análisis o datos crudos y los transformas en un resumen "
            "breve, profesional y persuasivo para un gerente, en español, máximo 150 palabras."
        ),
        "model": "llama3.2:3b",
        "temperature": 0.5,
        "tools": [],
    },
    {
        "name": "Asesor de Onboarding",
        "icon": "graduation-cap",
        "description": "Responde preguntas de nuevos colaboradores con el manual de bienvenida.",
        "role_prompt": (
            "Eres el asistente de onboarding de TCS. Respondes preguntas de nuevos empleados usando "
            "unicamente el contexto interno recuperado cuando este disponible. Si no encuentras la "
            "respuesta en el contexto, dilo con honestidad. Responde en español, de forma cercana y breve."
        ),
        "model": "llama3.2:3b",
        "temperature": 0.3,
        "tools": [],
    },
    {
        "name": "Asistente de RR.HH.",
        "icon": "users",
        "description": "Orienta sobre políticas, permisos y trámites de personal.",
        "role_prompt": (
            "Eres el asistente de Recursos Humanos de TCS. Respondes dudas sobre politicas internas, "
            "permisos y tramites de forma empatica y precisa, en español. Si una consulta requiere "
            "revision de un caso personal, recomiendas escribir a HR Connect."
        ),
        "model": "llama3.2:3b",
        "temperature": 0.4,
        "tools": ["fecha_actual"],
    },
    {
        "name": "Revisor de Contratos",
        "icon": "scale",
        "description": "Identifica cláusulas de riesgo y resume contratos con clientes.",
        "role_prompt": (
            "Eres un analista legal de TCS. Revisas textos contractuales, identificas clausulas de "
            "riesgo (penalidades, responsabilidad, confidencialidad, plazos) y las resumes en una tabla "
            "breve con nivel de riesgo. Responde en español y no inventes clausulas que no esten en el texto."
        ),
        "model": "llama3.2:3b",
        "temperature": 0.2,
        "tools": [],
        "status": "inactive",
    },
]

# Iconos para bases creadas con la version anterior, que usaba emojis.
LEGACY_ICONS = {"🛠️": "wrench", "📊": "chart-column", "📝": "file-text", "🎓": "graduation-cap"}

SAMPLE_HANDBOOK = """
Manual de Bienvenida - TCS (documento de referencia interno, version demo)

Politica de vacaciones: Los empleados de TCS acumulan 1.25 dias de vacaciones por mes trabajado,
hasta un maximo de 15 dias habiles al ano. Las solicitudes se hacen a traves del portal Ultimatix
con al menos 5 dias habiles de anticipacion.

Horario de trabajo: El horario estandar es de 9:00 a 18:00 de lunes a viernes, con esquema hibrido
de 3 dias en oficina y 2 dias remoto, sujeto a aprobacion del lider de proyecto.

Capacitacion obligatoria: Todo nuevo ingreso debe completar el modulo de Seguridad de la Informacion
y el modulo de Codigo de Conducta dentro de los primeros 15 dias, disponibles en TCS iEvolve.

Beneficios: TCS ofrece seguro medico privado, seguro de vida, y un bono anual de desempeno sujeto
a evaluacion. El programa de bienestar incluye acceso a gimnasios asociados y dias de salud mental.

Canal de soporte: Para dudas de TI, usar el Service Desk interno (ticket TCS-XXXX). Para dudas de
Recursos Humanos, escribir al buzon de HR Connect.
"""


def _seed_users(session: Session) -> None:
    for data in DEMO_USERS:
        user = session.exec(select(User).where(User.name == data["name"])).first()
        if not user:
            session.add(User(**data, password_hash=hash_password(DEMO_PASSWORD)))
            continue
        # Usuarios sembrados antes de existir el login: se completan sus credenciales.
        if not user.email:
            user.email = data["email"]
        if not user.password_hash:
            user.password_hash = hash_password(DEMO_PASSWORD)
        if user.is_active is None:
            user.is_active = True
        session.add(user)


def _seed_agents(session: Session) -> None:
    for agent in session.exec(select(Agent)).all():
        if agent.avatar_emoji in LEGACY_ICONS and agent.icon in (None, "", "bot"):
            agent.icon = LEGACY_ICONS[agent.avatar_emoji]
            session.add(agent)
        if agent.description.endswith("(RAG)."):
            agent.description = "Responde preguntas de nuevos colaboradores con el manual de bienvenida."
            session.add(agent)
    for data in DEMO_AGENTS:
        if not session.exec(select(Agent).where(Agent.name == data["name"])).first():
            session.add(Agent(**data, created_by="Ana Ríos"))


def _seed_activity(session: Session) -> None:
    """Historial de uso de los ultimos 30 dias para que el panel tenga contexto desde el inicio."""
    if session.exec(select(MetricLog)).first():
        return
    agents = [a for a in session.exec(select(Agent)).all() if a.status == "active"]
    users = session.exec(select(User)).all()
    if not agents or not users:
        return
    rng = random.Random(2026)
    weights = [5, 4, 3, 6, 2][: len(agents)] + [1] * max(0, len(agents) - 5)
    now = datetime.utcnow()
    for days_ago in range(29, -1, -1):
        day = now - timedelta(days=days_ago)
        weekday_factor = 0.35 if day.weekday() >= 5 else 1.0
        volume = int(rng.randint(14, 30) * weekday_factor * (1 + (29 - days_ago) / 45))
        for _ in range(volume):
            agent = rng.choices(agents, weights=weights)[0]
            prompt = rng.randint(280, 1500)
            completion = rng.randint(70, 520)
            success = rng.random() > 0.025
            ts = day.replace(hour=rng.randint(8, 19), minute=rng.randint(0, 59), second=rng.randint(0, 59))
            if ts > now:
                ts = now - timedelta(minutes=rng.randint(1, 120))
            session.add(MetricLog(
                agent_id=agent.id,
                agent_name=agent.name,
                user_id=rng.choices(users, weights=[2, 5, 3][: len(users)] + [1] * max(0, len(users) - 3))[0].id,
                model=agent.model,
                latency_ms=rng.randint(850, 4800),
                prompt_tokens=prompt if success else 0,
                completion_tokens=completion if success else 0,
                total_tokens=prompt + completion if success else 0,
                tool_calls=rng.choice([0, 0, 1]) if agent.tools else 0,
                success=success,
                error_message=None if success else "El motor de modelos no está disponible",
                created_at=ts,
            ))
    logger.info("Historial de actividad sembrado (30 dias).")


def run_seed() -> None:
    with Session(engine) as session:
        _seed_users(session)
        _seed_agents(session)
        session.commit()
        if SEED_DEMO_ACTIVITY:
            _seed_activity(session)
            session.commit()


async def seed_sample_knowledge() -> None:
    """Ingresa el manual de bienvenida de ejemplo al agente de Onboarding, si Ollama esta disponible."""
    if not await ollama_client.is_available():
        logger.warning("Ollama no disponible: se omite la carga del conocimiento de ejemplo (RAG).")
        return

    with Session(engine) as session:
        onboarding = session.exec(select(Agent).where(Agent.name == "Asesor de Onboarding")).first()
        if not onboarding:
            return
        existing = session.exec(
            select(KnowledgeDocument).where(KnowledgeDocument.agent_id == onboarding.id)
        ).first()
        if existing:
            return
        try:
            await rag.ingest_document(
                session, onboarding.id, "manual_bienvenida_tcs.txt", SAMPLE_HANDBOOK.encode("utf-8")
            )
            logger.info("Base de conocimiento de ejemplo cargada para 'Asesor de Onboarding'.")
        except Exception as exc:  # noqa: BLE001
            logger.warning("No se pudo cargar la base de conocimiento de ejemplo: %s", exc)
