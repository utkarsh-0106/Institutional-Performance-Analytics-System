"""SQLAlchemy engine and session factory (expire_on_commit=False for safe dict extraction)."""
from contextlib import contextmanager
from typing import Generator

from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import Session, sessionmaker

from config.settings import DATABASE_URL
from database.models import Base

_engine = None
_SessionLocal = None


def get_engine():
    global _engine
    if _engine is None:
        connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}
        _engine = create_engine(DATABASE_URL, connect_args=connect_args, echo=False)
    return _engine


def get_session_factory():
    global _SessionLocal
    if _SessionLocal is None:
        _SessionLocal = sessionmaker(
            bind=get_engine(),
            autocommit=False,
            autoflush=False,
            expire_on_commit=False,
        )
    return _SessionLocal


def init_db() -> None:
    engine = get_engine()
    Base.metadata.create_all(bind=engine)
    _ensure_rbac_schema(engine)


def _ensure_rbac_schema(engine) -> None:
    """Small, idempotent migration for the RBAC fields on existing databases."""
    inspector = inspect(engine)
    user_columns = {c["name"] for c in inspector.get_columns("users")} if "users" in inspector.get_table_names() else set()
    with engine.begin() as conn:
        if "institution_id" not in user_columns:
            conn.execute(text("ALTER TABLE users ADD COLUMN institution_id INTEGER"))

        # Migrate legacy role names to the three canonical roles.
        conn.execute(text("UPDATE users SET role = 'ADMIN' WHERE lower(role) IN ('admin', 'administrator')"))
        conn.execute(text("UPDATE users SET role = 'ANALYST' WHERE lower(role) = 'analyst'"))
        conn.execute(text("UPDATE users SET role = 'INSTITUTION' WHERE lower(role) IN ('institution_user', 'institution')"))
        conn.execute(text("UPDATE users SET institution_id = (SELECT id FROM institutions WHERE institutions.institution_name = users.linked_institution) WHERE role = 'INSTITUTION' AND institution_id IS NULL AND linked_institution IS NOT NULL"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS ix_users_institution_id ON users (institution_id)"))


@contextmanager
def get_db_session() -> Generator[Session, None, None]:
    session = get_session_factory()()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
