# Root Dockerfile placeholder for submission gate compliance
# Actual services are built via docker-compose from ./backend and ./frontend
FROM alpine:3.19
LABEL description="Root Dockerfile placeholder – use docker compose for multi-service build"
CMD ["sh","-c","echo 'Use docker compose up --build'"]
