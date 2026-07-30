# Docker Setup

## Purpose

Docker Compose starts the Review 1 React homepage, FastAPI service, and PostgreSQL 16 together. It contains no application database schema, AI, authentication, or business logic.

## Start Local Containers

```bash
docker compose up --build
```

The homepage is available at <http://localhost:3000>, the API at <http://localhost:8000>, and PostgreSQL at `localhost:5432`. The local database uses the preconfigured `bandhan` user and database.

## Stop Containers

```bash
docker compose down
```

To remove the local database volume as well, run `docker compose down -v`.
