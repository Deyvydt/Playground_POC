from sqlalchemy import inspect, text
from sqlmodel import SQLModel, Session, create_engine
from app.config import DATABASE_URL

connect_args = {"check_same_thread": False}
engine = create_engine(DATABASE_URL, echo=False, connect_args=connect_args)

# Columnas agregadas despues de la primera version: create_all no altera tablas existentes,
# asi que una base creada antes las necesita via ALTER TABLE.
_ADDED_COLUMNS = {
    "user": {
        "email": "VARCHAR DEFAULT ''",
        "password_hash": "VARCHAR DEFAULT ''",
        "is_active": "BOOLEAN DEFAULT 1",
        "created_at": "DATETIME",
        "last_login_at": "DATETIME",
    },
    "agent": {"icon": "VARCHAR DEFAULT 'bot'", "updated_at": "DATETIME"},
    "conversation": {"user_id": "INTEGER"},
    "metriclog": {"user_id": "INTEGER"},
}


def _migrate() -> None:
    inspector = inspect(engine)
    with engine.begin() as conn:
        for table, columns in _ADDED_COLUMNS.items():
            if not inspector.has_table(table):
                continue
            existing = {c["name"] for c in inspector.get_columns(table)}
            for name, ddl in columns.items():
                if name not in existing:
                    conn.execute(text(f'ALTER TABLE "{table}" ADD COLUMN {name} {ddl}'))


def init_db() -> None:
    SQLModel.metadata.create_all(engine)
    _migrate()


def get_session():
    with Session(engine) as session:
        yield session
