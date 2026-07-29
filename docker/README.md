# Docker Setup

## Purpose

Docker Compose defines the infrastructure baseline for Bandhan: a FastAPI-ready backend container and PostgreSQL 16. The backend is an intentional placeholder; no application source, API, schema, or business logic is included in Review 1.

## Start Local Containers

```bash
docker compose up --build
```

PostgreSQL listens on `localhost:5432` by default and uses the `bandhan` database. The backend reserves `localhost:8000` for the future FastAPI service. Override defaults in a local `.env` file:

```dotenv
POSTGRES_DB=bandhan
POSTGRES_USER=bandhan
POSTGRES_PASSWORD=replace-with-a-local-secret
POSTGRES_PORT=5432
BACKEND_PORT=8000
APP_ENV=development
```

Do not commit `.env` files or credentials.

## Stop Containers

```bash
docker compose down
```

To remove the local database volume as well, run `docker compose down -v`.
