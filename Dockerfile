# Stage 1: Build the Vite React Frontend
FROM node:20-alpine AS frontend-builder
WORKDIR /build/frontend
COPY frontend/package.json frontend/package-lock.json* ./
RUN npm install
COPY frontend/ ./
RUN npm run build

# Stage 2: Production Python Backend + Static UI
FROM python:3.12-slim
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install python dependencies
COPY backend/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend source, seed data, and scripts
COPY backend/ ./backend/
COPY scripts/ ./scripts/
COPY seed/ ./seed/
COPY pyproject.toml ./

# Copy built frontend assets to be served by FastAPI
COPY --from=frontend-builder /build/frontend/dist ./frontend/dist

ENV PORT=8000
ENV PYTHONPATH="/app/backend:/app"
EXPOSE 8000

CMD ["sh", "-c", "python -m uvicorn app.main:app --app-dir backend --host 0.0.0.0 --port ${PORT:-8000}"]
