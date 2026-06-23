# AI Project Idea Collector

AI Project Idea Collector is a self-hosted application for collecting AI projects from URLs and scheduled sources, enriching them with an OpenAI-compatible model, searching them by keywords or embeddings, and turning the collection into new project ideas.

## Features

- Manual collection from GitHub, Hugging Face, Hackster, YouTube, articles, documentation, and generic webpages
- Scheduled GitHub and RSS source collection
- AI summaries, classification, tags, difficulty, requirements, idea value, and inspired ideas
- Keyword and Qdrant-backed semantic search
- Grounded chat with project URL citations
- Source management and collection logs in PostgreSQL
- Dark, responsive Next.js dashboard
- Streamable HTTP MCP server for AI clients
- Optional bearer-token protection for the web API and MCP
- Docker Compose deployment and automatic GHCR image publishing

## Architecture

```text
Browser
  -> Next.js frontend :3000
       -> same-origin /backend-api proxy
            -> FastAPI backend :8000
                 -> PostgreSQL
                 -> Qdrant

Python worker
  -> scheduled source collection
  -> FastAPI collection services
  -> PostgreSQL / Qdrant
```

The stack uses Next.js 16, React 19, TypeScript, Tailwind CSS, FastAPI, PostgreSQL, Qdrant, APScheduler, and the official Python MCP SDK.

## Quick Start

### Requirements

- Docker Engine with Docker Compose v2
- A practical starting point is 2 CPU cores, 4 GB RAM, and 10 GB free disk space

### Install

```bash
git clone <repository-url>
cd collector
cp .env.example .env
```

Generate strong keys:

```bash
openssl rand -hex 32
```

Edit `.env` and set at least:

```dotenv
APP_API_KEY=replace-with-a-random-value
MCP_API_KEY=replace-with-a-different-random-value
POSTGRES_PASSWORD=replace-with-another-random-value
```

Start the stack:

```bash
docker compose pull
docker compose up -d
docker compose ps
```

Open [http://localhost:3000](http://localhost:3000) and enter `APP_API_KEY` on the unlock screen. The token remains in that browser's local storage.

Useful commands:

```bash
docker compose logs -f backend worker
docker compose restart backend worker
docker compose down
```

`docker compose down` preserves PostgreSQL and Qdrant volumes. Do not add `-v` unless you intend to delete all collected data.

## Configure AI

The application has two AI configurations because they perform different jobs:

- **LLM:** generates summaries, classifications, tags, ideas, and chat answers.
- **Embedding model:** converts text into vectors for semantic search.

Both can use the same provider, base URL, and API key, but they require different model names.

### Cheapest SiliconFlow Setup

Open **Settings** and use:

| Setting | Value |
| --- | --- |
| LLM base URL | `https://api.siliconflow.cn/v1` |
| LLM model | `Qwen/Qwen2.5-7B-Instruct` |
| Embedding provider | `openai` |
| Embedding base URL | `https://api.siliconflow.cn/v1` |
| Embedding model | `BAAI/bge-m3` |
| API keys | The same SiliconFlow key may be entered in both fields |

These two models are currently listed by SiliconFlow as free. Provider pricing and availability can change, so check the provider catalog before a large import.

Without AI credentials, collection still works using deterministic fallback classification. Semantic embeddings and model-generated chat require configured credentials.

Secrets entered in Settings are stored server-side in PostgreSQL and are never returned to the browser. They are currently stored as plaintext database values, so protect database access and backups.

### GitHub Token

Set `GITHUB_TOKEN` in `.env` to increase GitHub API limits and read selected private repositories.

Use a fine-grained token with only:

- Repository access: public repositories or only selected private repositories
- `Metadata`: read-only
- `Contents`: read-only

No write, Actions, administration, workflow, issue, or pull-request permissions are required. Restart `backend` and `worker` after changing this environment variable.

## Usage Guide

### Add a Project

1. Open **Dashboard**.
2. Paste a project URL into **Collect project**.
3. Wait for metadata extraction and AI enrichment.
4. Open the project from **Recently collected** or **Projects**.

If collection fails, the project detail records the error. The current MVP does not yet provide a reprocess button; delete and add the URL again after fixing the configuration.

### Add Automatic Sources

1. Open **Sources** and select **Add source**.
2. Choose a source type and enter its URL or query.
3. Set the refresh interval in minutes.
4. Use **Run now** for an immediate scan, or leave the source enabled for the worker.

GitHub user/search and RSS sources perform multi-item scans. Hackster, Hugging Face, YouTube, and blog adapters currently normalize a supplied page; provider-specific channel, organization, and tag enumeration remains future work.

### Search Projects

The **Projects** page supports keyword search, type/source/difficulty filters, sorting, and optional semantic search. Semantic search applies only to projects collected after a working embedding model was configured; the MVP does not yet include bulk reindexing.

### Chat With the Collection

Open **AI Chat** and ask questions such as:

- `Find edge AI projects using YOLO.`
- `Give me ideas based on robotics agents.`
- `Which projects could become technical wiki articles?`

Answers use collected project context and include links to original sources.

### Settings Behavior

Model URLs, keys, models, prompts, and auto-collection state are resolved for new jobs. Changing the PostgreSQL URL or global worker interval requires restarting the affected service.

## MCP Server

The backend exposes MCP Streamable HTTP at:

```text
http://localhost:8000/mcp
```

Available tools:

- `add_project`, `search_projects`, `get_project`, `delete_project`
- `list_sources`, `add_source`, `update_source`, `collect_source`

Set `MCP_API_KEY` to require:

```http
Authorization: Bearer <MCP_API_KEY>
```

Hosted ChatGPT or Gemini-compatible clients cannot reach `localhost`. Deploy the backend behind public HTTPS and point the client to `https://api.example.com/mcp`. A production multi-user integration should place an OAuth-capable gateway in front of this single-user bearer-token implementation.

## Production Deployment

### Docker Compose With Prebuilt Images

On a Linux server:

```bash
git clone <repository-url>
cd collector
cp .env.example .env
# Configure APP_API_KEY, MCP_API_KEY, POSTGRES_PASSWORD, AI credentials, and GitHub token.
docker compose pull
docker compose up -d
```

By default:

- Frontend listens on `127.0.0.1:3000`.
- Backend listens on `127.0.0.1:8000`.
- PostgreSQL and Qdrant listen on localhost only.

Do not expose ports `5432` or `6333` to the internet. Keep the frontend and backend on `127.0.0.1` when using host-level Nginx, Caddy, or Traefik. Set a bind address to `0.0.0.0` only when a firewall or containerized proxy requires it.

### Nginx Reverse Proxy

Put Nginx in front of the localhost-only Docker services:

```nginx
server {
    listen 80;
    server_name collector.example.com;

    location / {
        proxy_pass http://127.0.0.1:3000;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

If you want direct API or MCP access from ChatGPT, Gemini, or another external client, add a separate API hostname:

```nginx
server {
    listen 80;
    server_name collector-api.example.com;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

Then enable HTTPS:

```bash
sudo certbot --nginx -d collector.example.com -d collector-api.example.com
```

The frontend normally reaches FastAPI through its same-origin `/backend-api` proxy. The API domain is only required for direct OpenAPI or MCP access. Restrict `/docs` in a public deployment if it is not needed.

### Published Container Images

The workflow at `.github/workflows/docker-publish.yml` publishes two multi-architecture images to GitHub Container Registry after pushes to the default branch and tags matching `v*`:

```text
ghcr.io/hanzo-huang/ai-project-idea-collector/backend:latest
ghcr.io/hanzo-huang/ai-project-idea-collector/frontend:latest
```

The worker uses the backend image with a different command. After pushing this repository to GitHub, open **Actions** and confirm **Publish Docker images** succeeds. Make the packages public in the repository package settings, or authenticate the server with a GitHub token containing `read:packages`.

Container archives should not be committed to Git. GHCR stores versioned image layers next to the repository and is the appropriate distribution mechanism.

The workflow builds AMD64 on `ubuntu-24.04` and ARM64 on GitHub's native `ubuntu-24.04-arm` runner, then combines both digests into each published tag. This avoids the slow QEMU emulation that caused the earlier ARM64 frontend build to be canceled.

### Vercel Frontend

The Next.js frontend can be deployed separately to Vercel with `frontend/` as the project root. Set:

```dotenv
INTERNAL_API_URL=https://your-public-fastapi-host.example.com
```

FastAPI, the persistent worker, PostgreSQL, and Qdrant must still run on a container host or managed services. GitHub Pages cannot host the complete application because it only serves static files.

## Updates and Backups

Update a server deployment:

```bash
git pull
docker compose pull
docker compose up -d
```

Back up PostgreSQL:

```bash
docker compose exec -T postgres sh -c 'pg_dump -U "$POSTGRES_USER" -d "$POSTGRES_DB"' > collector-backup.sql
```

Restore into an empty database:

```bash
docker compose exec -T postgres sh -c 'psql -U "$POSTGRES_USER" -d "$POSTGRES_DB"' < collector-backup.sql
```

Also back up the `postgres_data` and `qdrant_data` Docker volumes before server migrations or destructive maintenance.

## Local Development

The default Compose file uses published images. To build local source changes into containers, add `docker-compose.build.yml`:

```bash
docker compose -f docker-compose.yml -f docker-compose.build.yml up -d --build
```

Start PostgreSQL and Qdrant:

```bash
docker compose up -d postgres qdrant
```

Run the backend and worker:

```bash
cd backend
python -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
# In a second activated shell:
python -m app.worker.main
```

Run the frontend:

```bash
cd frontend
npm ci
npm run dev
```

Local URLs:

- Dashboard: `http://localhost:3000`
- API docs: `http://localhost:8000/docs`
- Health: `http://localhost:8000/api/health`
- MCP: `http://localhost:8000/mcp`

## Testing

```bash
cd backend
python -m unittest discover -s tests -v
python -m compileall -q app

cd frontend
npm ci
npm run build

docker compose config --quiet
docker compose -f docker-compose.yml -f docker-compose.build.yml build
```

GitHub Actions runs backend tests and the frontend production build for pull requests and pushes to `main` or `master`.

## Troubleshooting

### Login says `Failed to fetch`

If you are developing locally, rebuild the frontend so it uses the same-origin API proxy:

```bash
docker compose -f docker-compose.yml -f docker-compose.build.yml up -d --build frontend
curl http://localhost:3000/backend-api/auth/status
```

The response should be `{"required":true}` when `APP_API_KEY` is configured.

### Backend cannot resolve `postgres`

`postgres` is a Compose-only hostname. Direct local backend processes should use `localhost` in `POSTGRES_URL`, with credentials matching `POSTGRES_USER`, `POSTGRES_PASSWORD`, and `POSTGRES_DB`; containers receive the internal hostname automatically.

### AI settings appear configured but semantic search is empty

Only newly enriched projects are embedded. Confirm the embedding base URL, key, and model, then collect a new project. Bulk reindexing is not implemented yet.

### GitHub collection is rate-limited

Add a fine-grained `GITHUB_TOKEN` with read-only Metadata and Contents access, then restart `backend` and `worker`.

## Security Notes

- Always set `APP_API_KEY` and `MCP_API_KEY` outside localhost.
- Keep `.env` out of Git; it is ignored by this repository.
- Never publish PostgreSQL or Qdrant ports.
- Generic webpage and RSS fetches reject private/local network addresses, revalidate redirects, accept text-like content only, and stop after 5 MB.
- Use HTTPS for remote access because browser and MCP bearer tokens must not travel over plaintext networks.
- Treat collected webpage text as untrusted external content.

## Current MVP Limitations

- Single-user authentication rather than accounts and roles
- No bulk embedding reindex or failed-project retry button
- Non-GitHub/RSS source adapters do not yet enumerate provider feeds
- Collection runs execute sequentially rather than through a distributed job queue
- Database schema changes use initialization/create-all rather than a complete Alembic migration history
