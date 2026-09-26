.PHONY: up down test lint seed export validate clean gate build-frontend

up:
	docker-compose up --build

down:
	docker-compose down -v

test:
	python -m pytest backend/tests

lint:
	ruff check backend

seed:
	python scripts/seed_database.py

export:
	curl -s http://localhost:8000/api/export -o labels.jsonl

validate:
	python downstream/validate_data.py labels.jsonl

gate:
	python verify_submission.py

build-frontend:
	cd frontend && npm run build

clean:
	python -c "import shutil, pathlib; [shutil.rmtree(p, ignore_errors=True) for p in pathlib.Path('.').rglob('__pycache__')]; [shutil.rmtree(p, ignore_errors=True) for p in pathlib.Path('.').rglob('.pytest_cache')]"
	python -c "import pathlib, os; [os.remove(f) for f in ('labels.jsonl', 'local_dev.db') if os.path.exists(f)]"
