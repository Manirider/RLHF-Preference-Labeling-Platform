# Database Migrations

Canonical Alembic migrations are located in `backend/alembic/versions/`.
Run migrations using Alembic:
```bash
alembic -c backend/alembic.ini upgrade head
```
Or let the backend service apply them automatically on application startup.
