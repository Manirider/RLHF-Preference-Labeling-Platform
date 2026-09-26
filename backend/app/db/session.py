import logging

from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

from app.core.config import settings

logger = logging.getLogger(__name__)

def get_engine_args(url: str):
    if url.startswith("sqlite"):
        return {"connect_args": {"check_same_thread": False}}
    return {"pool_pre_ping": True}

def create_resilient_engine(url: str):
    try:
        return create_engine(url, **get_engine_args(url))
    except (ModuleNotFoundError, Exception) as exc:
        logger.warning(
            f"Failed to initialize database engine with URL '{url}' ({exc}). "
            f"Falling back to local SQLite engine."
        )
        fallback_url = "sqlite:///./local_dev.db"
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
