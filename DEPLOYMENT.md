# Deploying Radarr

Radarr has five moving parts: Postgres, Redis, Qdrant, a Celery
beat/worker pair, and the Streamlit dashboard. Locally these all run via
`docker compose up`. For a public deployment, the split below keeps
things on free/cheap tiers.

## Option A — Railway (recommended, one platform for everything except the dashboard)

Railway can build straight from this repo's `Dockerfile` and run multiple
services from it with different start commands, plus managed Postgres and
Redis plugins.

1. **Create a new Railway project** from this GitHub repo.
2. **Add managed plugins**: Postgres and Redis (Railway provisions these
   and gives you connection env vars automatically — map them to
   `POSTGRES_URL` / `REDIS_URL` in step 4).
3. **Add a Qdrant service**: Railway supports deploying arbitrary Docker
   images — use the `qdrant/qdrant` image directly (same as
   `docker-compose.yml`) rather than the app `Dockerfile`.
4. **Add three services built from this repo's `Dockerfile`**, each with
   a different start command:
   - `worker` → `celery -A pipeline.scheduler.celery_app worker --loglevel=info`
   - `scheduler` → `celery -A pipeline.scheduler.celery_app beat --loglevel=info`
   - `pipeline-once` (optional, for manual/on-demand runs) → `python -m pipeline.graph`
5. **Set environment variables** on every service (Railway lets you share
   a variable group across services): `GEMINI_API_KEY`, `POSTGRES_URL`,
   `REDIS_URL`, `QDRANT_URL`, `SLACK_WEBHOOK_URL`, `LOGFIRE_TOKEN`, and
   `USE_HOSTED_LLM=true` (see note below on why).
6. Deploy. Railway builds the `Dockerfile` once and reuses the image
   across the three services.

### Why `USE_HOSTED_LLM=true` for the deployed version

Locally, the Summarizer agent and the RAG chat use Ollama (`llama3.1:8b`)
running on your machine — free, but it needs ~5GB RAM and no GPU is
required, which most free/hobby cloud tiers don't comfortably give you as
a *long-running background process* alongside everything else. Setting
`USE_HOSTED_LLM=true` in `.env` makes `config/llm.py`'s `get_local_llm()`
fall back to Gemini Flash instead, with the same `.invoke()` string
interface — no other code changes needed. This is a deliberate
cost/hosting tradeoff, not a workaround: document it as such in your
README/demo — it's a legitimate "local-first, cloud-portable" design
decision, and Gemini's free tier (250 req/day) comfortably covers a
portfolio demo's traffic.

If you'd rather keep the local-LLM story intact for the deployed demo,
Railway also supports persistent volumes and larger instance types where
you could self-host Ollama as a sixth service — the docker-compose
pattern extends the same way, it's just a bigger box.

## Option B — Fly.io

Same shape as Railway: `fly launch` picks up the `Dockerfile`, add
Postgres/Redis via `fly postgres create` / a Redis app, and run the
worker/beat processes via `fly.toml`'s `[processes]` block instead of
separate services.

## Dashboard: Streamlit Community Cloud

The Streamlit dashboard (`dashboard/app.py`) is best deployed separately
on [Streamlit Community Cloud](https://streamlit.io/cloud) (free, purpose
-built for this):

1. Connect this GitHub repo, set the main file path to `dashboard/app.py`.
2. Add the same env vars as above (`POSTGRES_URL`, `QDRANT_URL`,
   `GEMINI_API_KEY`, `USE_HOSTED_LLM=true`) in the app's Secrets manager.
3. Since Postgres/Qdrant are now on Railway, make sure their connection
   URLs are the **public** Railway-provided endpoints, not the internal
   `postgres.railway.internal`-style hostnames (those only resolve inside
   Railway's private network).

## Local development

Nothing above changes local dev — `docker compose up` still brings up
Postgres/Redis/Qdrant plus the `pipeline`, `scheduler`, `worker`, and
`dashboard` app services defined in `docker-compose.yml`, all wired to
read from your local `.env` (based on `.env.example`).
