#!/usr/bin/env python3
"""
Seed data generation pipeline.
Loads seed prompts, generates pairwise model responses, and populates the database.
"""
import csv
import json
import logging
import os
import sys

# Ensure project root and backend are on PYTHONPATH
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(CURRENT_DIR, ".."))
BACKEND_DIR = os.path.join(PROJECT_ROOT, "backend")

if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

from app.db.session import Base, SessionLocal, engine
from app.models.models import Pair
from app.services.llm_service import generate_pair_responses

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

def load_seed_prompts():
    """Load prompts from JSON if available, otherwise CSV."""
    json_path = os.path.join(PROJECT_ROOT, "seed", "prompts.json")
    csv_path = os.path.join(PROJECT_ROOT, "seed", "prompts.csv")

    if os.path.exists(json_path):
        with open(json_path, encoding="utf-8") as f:
            return json.load(f)
    elif os.path.exists(csv_path):
        prompts = []
        with open(csv_path, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                prompts.append(row)
        return prompts
    else:
        raise FileNotFoundError(f"No seed prompts found at {json_path} or {csv_path}")

def generate_and_seed(db_session=None):
    """Generate responses for prompts and seed the database idempotently."""
    prompts = load_seed_prompts()
    logger.info(f"Loaded {len(prompts)} seed prompts.")

    # Ensure tables exist
    Base.metadata.create_all(bind=engine)

    close_session = False
    if db_session is None:
        db_session = SessionLocal()
        close_session = True

    try:
        inserted = 0
        skipped = 0
        for item in prompts:
            prompt_text = item["prompt"].strip()
            category = item.get("category", "general").strip()

            existing = db_session.query(Pair).filter(Pair.prompt == prompt_text).first()
            if existing:
                skipped += 1
                continue

            resp_a, resp_b = generate_pair_responses(prompt_text, category)
            pair = Pair(
                prompt=prompt_text,
                response_a=resp_a,
                response_b=resp_b,
                category=category
            )
            db_session.add(pair)
            inserted += 1

        db_session.commit()
        total_count = db_session.query(Pair).count()
        logger.info(f"Seed complete: {inserted} inserted, {skipped} already present. Total pairs in DB: {total_count}")
        return total_count
    except Exception as e:
        db_session.rollback()
        logger.error(f"Error during seeding: {e}")
        raise
    finally:
        if close_session:
            db_session.close()

def main():
    logger.info("Starting seed data generation...")
    generate_and_seed()
    logger.info("Generation completed successfully.")

if __name__ == "__main__":
    main()
