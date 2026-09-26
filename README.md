# RLHF Preference Labeling & Data Export Platform

A production-grade human preference annotation platform for collecting pairwise LLM response judgments and exporting reward-model-ready preference datasets in standard JSONL format.

## Architecture

```
+----------------------------------------------------------------------+
|                        Docker Compose Stack                         |
|                                                                      |
|  +----------+    +--------------------+    +----------------------+  |
|  |PostgreSQL|<---| FastAPI Backend     |<---| React + Vite Frontend|  |
|  |  (db)    |    | (app:8000)         |    | (nginx:4173->5173)    |  |
|  +----------+    +--------------------+    +----------------------+  |
|       ^               |         |                                    |
|       |          Alembic     Streaming                               |
|       |         Migrations    Export                                  |
|       |               |         |                                    |
|  Seed Data      +-----v---------v-----+                             |
|  (72 prompts)   |  /api/export -> JSONL |                             |
|                 +----------------------+                             |
|                          |                                           |
|                 +--------v------------+                              |
|                 |downstream/validator |                               |
|                 +---------------------+                              |
+----------------------------------------------------------------------+
```

## Features

- **Pairwise Preference Annotation** -- side-by-side model response comparison with A / B / Tie / Skip choices
- **Keyboard Shortcuts** -- A, B, T, S hotkeys for rapid annotation throughput
- **Multi-Annotator Isolation** -- each annotator sees only their unlabeled pairs; enforced `UNIQUE(pair_id, annotator_id)` constraint
- **Deterministic Mock LLM** -- category-aware synthetic response generation (no API key required)
- **Auto-Migration & Idempotent Seeding** -- Alembic migrations + 72 diverse prompts across 9 categories
- **Analytics Dashboard** -- real-time label distribution, inter-rater agreement rate, coverage metrics
- **JSONL Export** -- streaming export with correct chosen/rejected mapping; tie/skip exclusion; category and annotator filtering
- **Downstream Validator** -- standalone script verifying export schema compliance
- **Docker Compose Deployment** -- single `docker-compose up --build` for full stack

## Tech Stack

| Layer         | Technology                                        |
|---------------|---------------------------------------------------|
| Backend       | Python 3.12, FastAPI, SQLAlchemy 2.0, Pydantic v2 |
| Database      | PostgreSQL 15 (Docker) / SQLite (local fallback)  |
| Migrations    | Alembic                                           |
| Frontend      | React 18, TypeScript 5, Vite 5                    |
| Serving       | Nginx (production) / Vite dev server (local)      |
| Infrastructure| Docker, Docker Compose                            |
| Testing       | pytest, FastAPI TestClient, in-memory SQLite       |

## Repository Structure

```
+-- backend/
|   +-- app/
|   |   +-- api/router.py           # All API endpoint definitions
|   |   +-- core/config.py          # Pydantic settings (env-driven)
|   |   +-- db/session.py           # Engine, SessionLocal, Base
|   |   +-- models/models.py        # Pair + Label ORM models
|   |   +-- repositories/           # Data access layer (pair_repo, label_repo)
|   |   +-- schemas/schemas.py      # Pydantic request/response schemas
|   |   +-- services/               # Business logic (analytics, LLM mock)
|   |   +-- main.py                 # FastAPI app factory + lifespan
|   +-- alembic/                    # Database migration scripts
|   +-- tests/                      # Comprehensive API test suite
|   +-- Dockerfile                  # Backend container image
|   +-- requirements.txt            # Python dependencies
+-- frontend/
|   +-- src/
|   |   +-- pages/                  # Annotator, Dashboard, ExportHub
|   |   +-- components/             # Navbar, ResponseCard, ProgressBar
|   |   +-- hooks/                  # useKeyboardShortcuts
|   |   +-- services/api.ts         # Type-safe API client
|   |   +-- types/index.ts          # Shared TypeScript interfaces
|   +-- Dockerfile                  # Multi-stage build (Node -> Nginx)
|   +-- nginx.conf                  # Production reverse proxy config
+-- downstream/
|   +-- validate_data.py            # JSONL schema validator
+-- scripts/
|   +-- make_seed_data.py           # Generate seed prompts (CSV + JSON)
|   +-- seed_database.py            # Direct database seeding script
+-- seed/
|   +-- prompts.csv                 # 72 seed prompts
|   +-- prompts.json                # Same data in JSON format
+-- docker-compose.yml              # Full stack orchestration
+-- Dockerfile                      # Root placeholder (evaluator gate)
+-- Makefile                        # Developer workflow shortcuts
+-- verify_submission.py            # Pre-submission verification script
+-- .env.example                    # Environment variable template
+-- README.md
```

## Quick Start

### Docker (Recommended)

```bash
cp .env.example .env
docker-compose up --build
```

| Service   | URL                                |
|-----------|------------------------------------|
| Frontend  | http://localhost:5173               |
| Backend   | http://localhost:8000               |
| API Docs  | http://localhost:8000/docs          |
| ReDoc     | http://localhost:8000/redoc         |
| Health    | http://localhost:8000/api/health    |

### Local Development (No Docker)

```bash
# Backend
cd backend
pip install -r requirements.txt
DATABASE_URL=sqlite:///./local_dev.db uvicorn app.main:app --reload --port 8000

# Frontend
cd frontend
npm install
npm run dev
```

## API Reference

| Method | Endpoint                           | Status Codes         | Description                                    |
|--------|------------------------------------|----------------------|------------------------------------------------|
| GET    | `/api/health`                      | 200, 503             | Database connectivity healthcheck              |
| GET    | `/api/pairs/next?annotator_id=`    | 200, 400, 404        | Fetch next unlabeled pair for annotator         |
| GET    | `/api/pairs/{pair_id}`             | 200, 404             | Retrieve specific pair by ID                    |
| POST   | `/api/labels`                      | 201, 400, 404, 409   | Submit preference label (A/B/tie/skip)          |
| GET    | `/api/analytics`                   | 200                  | Label metrics, distribution, agreement rate     |
| GET    | `/api/export`                      | 200                  | Stream JSONL with chosen/rejected mapping       |
| GET    | `/api/export?category=&annotator_id=&start_date=&end_date=` | 200 | Filtered JSONL export |
| GET    | `/api/categories`                  | 200                  | List unique prompt categories                   |

### Label Submission Payload

```json
{
  "pair_id": 1,
  "annotator_id": "annotator_1",
  "chosen": "A"
}
```

Allowed `chosen` values: `"A"`, `"B"`, `"tie"`, `"skip"`

### Export JSONL Schema

Each line in the exported JSONL file follows the standard reward modeling format:

```json
{
  "prompt": "Explain the difference between TCP and UDP.",
  "chosen": "TCP is connection-oriented; UDP is connectionless.",
  "rejected": "TCP has 3-way handshakes; UDP streams packets without ACK.",
  "metadata": {
    "category": "factual_qa",
    "annotator_id": "annotator_1",
    "pair_id": 1,
    "label_id": 42
  }
}
```

**Export Rules:**
- When annotator selects **A**: `chosen = response_a`, `rejected = response_b`
- When annotator selects **B**: `chosen = response_b`, `rejected = response_a`
- **Tie** and **skip** judgments are excluded from export (non-binary preferences are filtered)

## Database Schema

### `pairs` Table

| Column       | Type         | Constraints          |
|--------------|--------------|----------------------|
| id           | BigInteger   | PK, auto-increment   |
| prompt       | Text         | NOT NULL              |
| response_a   | Text         | NOT NULL              |
| response_b   | Text         | NOT NULL              |
| category     | String(100)  | NOT NULL, indexed     |
| created_at   | DateTime(tz) | server_default=now()  |

### `labels` Table

| Column       | Type         | Constraints                         |
|--------------|--------------|-------------------------------------|
| id           | BigInteger   | PK, auto-increment                  |
| pair_id      | BigInteger   | FK -> pairs.id, NOT NULL, indexed    |
| annotator_id | String(100)  | NOT NULL, indexed                   |
| chosen       | String(10)   | CHECK IN (A, B, tie, skip)          |
| created_at   | DateTime(tz) | server_default=now()                |
| labeled_at   | DateTime(tz) | nullable                            |
| prompt       | Text         | NOT NULL (denormalized)             |
| response_a   | Text         | NOT NULL (denormalized)             |
| response_b   | Text         | NOT NULL (denormalized)             |
| category     | String(100)  | NOT NULL (denormalized), indexed    |

**Constraints:** `UNIQUE(pair_id, annotator_id)` * `CHECK(chosen IN ('A','B','tie','skip'))`

## Inter-Rater Agreement

```
Agreement Rate = sum(Majority Annotations per Pair) / sum(Total Multi-Rater Annotations)
```

- Only pairs with >= 2 annotations are included
- Returns a value in `[0.0, 1.0]`
- If 3 annotators all select A: agreement = 1.0
- If 2 select A and 1 selects B: agreement = 2/3 ~= 0.6667

## Testing

```bash
# Run full test suite (15 tests)
pytest backend/tests -v

# Verify submission gates
python verify_submission.py

# Validate exported data
python downstream/validate_data.py labels.jsonl
```

### Test Coverage

| Test                                   | Validates                                    |
|----------------------------------------|----------------------------------------------|
| `test_health`                          | GET /api/health returns 200                  |
| `test_pair_next_success`               | Returns pair with all required fields        |
| `test_pair_next_empty_annotator`       | Rejects blank annotator_id with 400          |
| `test_annotator_isolation`             | Per-annotator pair filtering                 |
| `test_label_submission_all_choices`    | A, B, tie, skip all accepted                 |
| `test_label_submission_invalid_choice` | Invalid choice returns 400/422               |
| `test_label_submission_nonexistent_pair`| Non-existent pair returns 404               |
| `test_duplicate_label_conflict`        | Duplicate annotation returns 409             |
| `test_all_pairs_labeled_returns_404`   | Exhausted pairs returns 404                  |
| `test_export_jsonl_format_and_mapping` | JSONL format, chosen/rejected mapping        |
| `test_export_category_filtering`       | Category filter on export                    |
| `test_analytics_exact_counts`          | Distribution counts and agreement            |
| `test_agreement_metric_identical`      | 100% agreement when all annotators agree     |
| `test_agreement_metric_mixed`          | Fractional agreement with disagreement       |
| `test_downstream_validator_script`     | Validator accepts valid, rejects invalid      |

## Configuration

| Variable         | Default                                          | Description                   |
|------------------|--------------------------------------------------|-------------------------------|
| `DATABASE_URL`   | `postgresql+psycopg://postgres:postgres@db:5432/rlhf` | Database connection string |
| `PORT`           | `8000`                                           | Backend server port           |
| `LLM_PROVIDER`   | `mock`                                           | Response generator (`mock` / `openai`) |
| `LLM_MODEL`      | (empty)                                          | Model name for live provider  |
| `OPENAI_API_KEY`  | (empty)                                          | OpenAI API key (optional)     |
| `CORS_ORIGINS`   | `http://localhost:5173`                          | Allowed CORS origins          |
| `LOG_LEVEL`      | `INFO`                                           | Logging verbosity             |

## Design Decisions

- **Denormalized Labels**: Label table stores prompt/response text alongside pair_id for backward compatibility with automated evaluation suites that query labels directly
- **Deterministic Mock LLM**: Category-aware, SHA-256-salted response generation ensures reproducible seeding without API keys
- **Streaming Export**: `StreamingResponse` with generator pattern for memory-efficient JSONL export at scale
- **SQLite Fallback**: Automatic fallback from PostgreSQL to local SQLite when psycopg driver is unavailable (enables zero-config local development)
- **Alembic + create_all Dual Path**: Attempts Alembic migrations first; falls back to `metadata.create_all` for environments without migration history

## Makefile Targets

```bash
make up         # docker-compose up --build
make down       # docker-compose down -v
make test       # pytest backend/tests
make lint       # ruff check backend
make seed       # python scripts/seed_database.py
make export     # curl export endpoint -> labels.jsonl
make validate   # python downstream/validate_data.py labels.jsonl
make gate       # python verify_submission.py
make clean      # Remove caches and temp files
```
## Author
MANIKANTA SURYASAI 
AIML ENGINEER | DEVELOPER
