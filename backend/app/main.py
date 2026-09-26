import logging
import os
from contextlib import asynccontextmanager

from alembic import command
from alembic.config import Config
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from app.api.router import router
from app.core.config import settings
from app.db.session import Base, SessionLocal, engine
from app.models.models import Pair

logging.basicConfig(
    level=getattr(logging, settings.log_level.upper(), logging.INFO),
    format="%(asctime)s [%(levelname)s] [%(name)s] %(message)s"
)
logger = logging.getLogger("rlhf_platform")

def run_migrations():
    """Execute Alembic migrations to align database schema to head."""
    if not str(engine.url).startswith("sqlite"):
        ini_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "alembic.ini"))
        if os.path.exists(ini_path):
            try:
                logger.info("Applying Alembic database migrations...")
                cfg = Config(ini_path)
                alembic_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "alembic"))
                cfg.set_main_option("script_location", alembic_dir)
                cfg.set_main_option("sqlalchemy.url", str(engine.url))
                command.upgrade(cfg, "head")
                logger.info("Alembic migrations completed successfully.")
                return
            except Exception as e:
                logger.warning(f"Alembic migration encountered an error ({e}); falling back to metadata create_all.")
    Base.metadata.create_all(bind=engine)
    logger.info("Database schema initialized via metadata.create_all.")

def seed_if_needed():
    """Ensure database has at least 50 prompt-response pairs idempotently on startup."""
    run_migrations()
    session = SessionLocal()
    try:
        current_count = session.query(Pair).count()
        if current_count >= 50:
            logger.info(f"Database already contains {current_count} pairs (>= 50 required). Skipping seed.")
            return

        logger.info(f"Current pair count is {current_count} (< 50). Executing automatic seed...")
        # Import seed logic
        import json

        from app.services.llm_service import generate_pair_responses

        # Look for seed/prompts.json or csv in project root or relative
        possible_paths = [
            os.path.join(os.path.dirname(__file__), "..", "..", "seed", "prompts.json"),
            os.path.join(os.path.dirname(__file__), "..", "seed", "prompts.json"),
            os.path.join("/app", "seed", "prompts.json"),
            os.path.join(os.getcwd(), "seed", "prompts.json"),
        ]
        prompts = []
        for p in possible_paths:
            if os.path.exists(p):
                with open(p, encoding="utf-8") as f:
                    prompts = json.load(f)
                break

        # Fallback prompts if seed file not mounted
        if not prompts:
            logger.warning("Seed prompts file not found; using fallback prompt catalog.")
            prompts = [
                {"prompt": f"Technical prompt #{i}: Explain key system engineering considerations for task {i}.", "category": "factual_qa"}
                for i in range(1, 60)
            ]

        inserted = 0
        for item in prompts:
            prompt_text = item["prompt"].strip()
            cat = item.get("category", "general")
            if session.query(Pair).filter(Pair.prompt == prompt_text).first():
                continue
            resp_a, resp_b = generate_pair_responses(prompt_text, cat)
            pair = Pair(
                prompt=prompt_text,
                response_a=resp_a,
                response_b=resp_b,
                category=cat
            )
            session.add(pair)
            inserted += 1

        session.commit()
        final_count = session.query(Pair).count()
        logger.info(f"Seed complete. Inserted {inserted} new pairs. Total pairs: {final_count}")
    except Exception as e:
        session.rollback()
        logger.error(f"Error during automatic seeding: {e}", exc_info=True)
    finally:
        session.close()

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager: runs migrations and seeding on startup."""
    logger.info("Starting RLHF Preference Labeling Platform...")
    try:
        seed_if_needed()
    except Exception as e:
        logger.error(f"Startup initialization error: {e}", exc_info=True)
    yield
    logger.info("Shutting down RLHF Preference Labeling Platform...")

app = FastAPI(
    title="RLHF Preference Labeling Platform",
    description="Production-grade platform for collecting pairwise preference annotations and exporting reward-model training data.",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# CORS Middleware
origins = settings.cors_origins_list
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins if origins else ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Exception handling middleware
@app.middleware("http")
async def error_handling_middleware(request: Request, call_next):
    try:
        return await call_next(request)
    except Exception as exc:
        logger.error(f"Unhandled exception processing {request.method} {request.url.path}: {exc}", exc_info=True)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"detail": "Internal server error occurred."}
        )

# Register API Router
app.include_router(router, prefix="/api")

# Serve frontend static assets & SPA when dist is present
possible_dist_dirs = [
    os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "frontend", "dist")),
    os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "frontend", "dist")),
    "/app/frontend/dist",
]
frontend_dist = next((d for d in possible_dist_dirs if os.path.exists(d)), None)

if frontend_dist:
    assets_dir = os.path.join(frontend_dist, "assets")
    if os.path.exists(assets_dir):
        app.mount("/assets", StaticFiles(directory=assets_dir), name="assets")

    @app.get("/{full_path:path}")
    async def serve_spa(full_path: str):
        target = os.path.join(frontend_dist, full_path)
        if full_path and os.path.isfile(target):
            return FileResponse(target)
        index_file = os.path.join(frontend_dist, "index.html")
        if os.path.exists(index_file):
            return FileResponse(index_file)
        return JSONResponse(status_code=404, content={"detail": "Not found"})
