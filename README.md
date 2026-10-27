# JobFit

JobFit scores how well a resume fits a job description, explains each gap, suggests grounded bullet edits, and answers questions in a cited chat.

**Stack:** FastAPI · Celery + RabbitMQ · Postgres + pgvector · Sentence Transformers (local embeddings) · Claude API · React + Vite + TypeScript

## Run it

Prerequisite: [Docker Desktop](https://www.docker.com/products/docker-desktop/).

```bash
cp .env.example .env        # then set ANTHROPIC_API_KEY and JWT_SECRET
docker compose up --build
```

| Service | URL |
|---|---|
| Frontend | http://localhost:5173 |
| API docs (Swagger) | http://localhost:8000/docs |
| RabbitMQ UI | http://localhost:15672 (guest / guest) |

The first worker start downloads the embedding model (~90 MB) into the `modelcache` volume.

## Try the API (week 1)

From http://localhost:8000/docs:

1. `POST /auth/register`, then `POST /auth/login` → copy `access_token` into **Authorize**.
2. `POST /resumes` with a PDF → returns a `task_id`.
3. `GET /tasks/{task_id}` until `status` is `done`, then `GET /resumes/{result_ref}`.
4. `POST /jobs` with a pasted job description, and poll the same way.

## Tests

```bash
docker compose run --rm api pytest
```

## Layout

```
backend/    FastAPI app (app/), Celery worker (worker/), Alembic migrations, tests
frontend/   React SPA
eval/       labelled resume/JD pairs for the evaluation page
docs/       design documents
```

## Status

- [x] Week 1: Compose, auth, PDF parsing, embeddings, resume and job parsing tasks
- [ ] Week 2: match analysis and score breakdown; login, upload, and analysis screens
- [ ] Week 3: SSE chat with citations; grounded bullet suggestions; retries and the dead-letter queue
- [ ] Week 4: evaluation page, tests, and demo video
