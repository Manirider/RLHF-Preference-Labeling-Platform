import logging
import os

from sqlalchemy import create_engine, text
from sqlalchemy.orm import declarative_base, sessionmaker

from app.core.config import settings

logger = logging.getLogger(__name__)

def get_engine_args(url: str):
    if url.startswith("sqlite"):
        return {"connect_args": {"check_same_thread": False}}
    return {
        "pool_pre_ping": True,
        "connect_args": {"connect_timeout": 5}
    }

def create_resilient_engine(url: str):
    # Normalize Render / Heroku postgres:// URLs to SQLAlchemy compatible format
    if url.startswith("postgres://"):
        url = url.replace("postgres://", "postgresql+psycopg://", 1)
    elif url.startswith("postgresql://") and "+" not in url.split("://")[0]:
        url = url.replace("postgresql://", "postgresql+psycopg://", 1)

    if "render.com" in url and "sslmode" not in url:
        separator = "&" if "?" in url else "?"
        url = f"{url}{separator}sslmode=require"

    if url.startswith("sqlite"):
        return create_engine(url, **get_engine_args(url))

    try:
        eng = create_engine(url, **get_engine_args(url))
        with eng.connect() as conn:
            conn.execute(text("SELECT 1"))
        return eng
    except Exception as exc:
        logger.warning(
            f"Failed to connect to database with URL '{url}' ({exc}). "
            f"Falling back to local SQLite engine."
        )
        project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
        fallback_path = os.path.join(project_root, "local_dev.db").replace("\\", "/")
        fallback_url = f"sqlite:///{fallback_path}"
        return create_engine(fallback_url, **get_engine_args(fallback_url))

engine = create_resilient_engine(settings.database_url)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

