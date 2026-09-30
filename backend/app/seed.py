import logging
from sqlmodel import Session, select
from app.database import engine
from app.models import User, Agent
from app import rag, ollama_client

logger = logging.getLogger("seed")

DEMO_USERS = [
    {"name": "Ana Ríos", "role": "admin", "avatar_emoji": "👩‍💼", "title": "Gerente Regional"},
    {"name": "Carlos Vega", "role": "developer", "avatar_emoji": "🧑‍💻", "title": "AI Engineer"},
    {"name": "Lucía Soto", "role": "viewer", "avatar_emoji": "🙋‍♀️", "title": "Analista de Negocio"},
]

DEMO_AGENTS = [
    {
        "name": "Soporte TI",
        "avatar_emoji": "🛠️",
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
        "avatar_emoji": "📊",
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
        "avatar_emoji": "📝",
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
        "avatar_emoji": "🎓",
        "description": "Responde preguntas de nuevos empleados usando el manual interno (RAG).",
        "role_prompt": (
            "Eres el asistente de onboarding de TCS. Respondes preguntas de nuevos empleados usando "
            "unicamente el contexto interno recuperado cuando este disponible. Si no encuentras la "
            "respuesta en el contexto, dilo con honestidad. Responde en español, de forma cercana y breve."
        ),
        "model": "llama3.2:3b",
        "temperature": 0.3,
        "tools": [],
    },
]

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


def run_seed() -> None:
    with Session(engine) as session:
        if session.exec(select(User)).first():
            return  # ya sembrado

        for u in DEMO_USERS:
            session.add(User(**u))

        agent_objs = []
        for a in DEMO_AGENTS:
            agent = Agent(**a, created_by="Ana Ríos")
            session.add(agent)
            agent_objs.append(agent)
        session.commit()
        for a in agent_objs:
            session.refresh(a)

        logger.info("Datos de demo sembrados: %d usuarios, %d agentes", len(DEMO_USERS), len(agent_objs))


async def seed_sample_knowledge() -> None:
    """Ingresa el manual de bienvenida de ejemplo al agente de Onboarding, si Ollama esta disponible."""
    if not await ollama_client.is_available():
        logger.warning("Ollama no disponible: se omite la carga del conocimiento de ejemplo (RAG).")
        return

    with Session(engine) as session:
        onboarding = session.exec(select(Agent).where(Agent.name == "Asesor de Onboarding")).first()
        if not onboarding:
            return
        from app.models import KnowledgeDocument
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
