# CLAUDE.md — Lean LiteLLM Docker Stack

## Project Overview

Docker Compose stack for a local LiteLLM proxy with persistent Postgres and Redis. The setup is intentionally minimal: three services only, no monitoring plane, and no exporter sidecars.

This repository is infrastructure-only. There is no application code.

## Common Commands

```bash
# Validate the rendered compose file
docker compose config

# Start the stack
docker compose up -d

# Stop without removing data
docker compose down

# Stop and remove all persistent data
docker compose down -v

# Follow logs
docker compose logs -f litellm
docker compose logs -f postgres
docker compose logs -f redis

# Inspect target health
docker compose ps
```

## Service Endpoints

| Service | URL / Address | Notes |
|---|---|---|
| LiteLLM UI | http://localhost:4000/ui | Use `LITELLM_MASTER_KEY` |
| LiteLLM API | http://localhost:4000 | Bearer token = `LITELLM_MASTER_KEY` |
| PostgreSQL | 127.0.0.1:5432 | `POSTGRES_USER` / `POSTGRES_PASSWORD` |
| Redis | 127.0.0.1:6379 | `REDIS_PASSWORD` |

## Architecture

### Services

`litellm-proxy` depends on `postgres` and `redis`. All three services share the `litellm-net` bridge network and communicate by service name.

### Startup order

```
postgres (healthy) ─┐
                    ├─► litellm
redis (healthy)  ───┘
```

### Network

All containers share `litellm-net` and communicate by service name. LiteLLM, Postgres, and Redis publish host ports; Postgres and Redis stay bound to `127.0.0.1`.

`extra_hosts: host.docker.internal:host-gateway` remains enabled for LiteLLM so it can reach host-based model runtimes when needed.

## Configuration

### File map

| File | Purpose |
|---|---|
| `docker-compose.yaml` | Service definitions, networking, ports, healthchecks |
| `litellm-config.yaml` | LiteLLM models, DB, and Redis cache settings |
| `.env` | Local machine secrets and runtime values |
| `.env.example` | Safe placeholder template |

### Adding a new model

Add the model under `model_list` in `litellm-config.yaml`, then restart LiteLLM:

```bash
docker compose restart litellm
```

## Verification Workflow

### 1. Validate config

```bash
docker compose config
```

### 2. Start the stack

```bash
docker compose up -d
```

### 3. Check health

```bash
docker compose ps
```

Expected steady-state:

- `litellm`, `postgres`, and `redis` are healthy

## Environment Variables

`.env` is for local machine use only and should be treated as secret material. Use `.env.example` as the checked-in template.

Key variables:

| Variable | Purpose |
|---|---|
| `LITELLM_MASTER_KEY` | LiteLLM admin/auth key |
| `LITELLM_SALT_KEY` | DB encryption salt for stored provider secrets |
| `POSTGRES_DB`, `POSTGRES_USER`, `POSTGRES_PASSWORD` | Postgres connection settings |
| `REDIS_PASSWORD` | Redis auth password |
| `GEMINI_API_KEY`, `OPENAI_API_KEY` | Optional upstream provider keys used by the sample config |
| `TZ` | Container timezone |

## Important Caveats

### `LITELLM_SALT_KEY` is immutable

Once LiteLLM has stored encrypted provider keys in Postgres, changing `LITELLM_SALT_KEY` makes those saved secrets unreadable.

### Anthropic header forwarding stays enabled

`forward_client_headers_to_llm_api: true` is intentionally kept on so Anthropic beta headers continue to pass through the proxy.

### No observability sidecars by design

This stack intentionally omits Prometheus, Grafana, and exporters to keep local development lighter and easier to reason about. If you later want observability back, add it as a separate concern instead of bundling it into the default compose path.

### Claude Connectivity
Ensure to add the 
"env": {
    "ANTHROPIC_BASE_URL": "http://localhost:4000",
    "ANTHROPIC_AUTH_TOKEN": "<LITELLM_MASTER_KEY> | <LITELLM_VIRTUAL_KEY>",
    "ANTHROPIC_CUSTOM_HEADERS" : "x-litellm-api-key: <LITELLM_MASTER_KEY> | <LITELLM_VIRTUAL_KEY>",
    "OPENAI_BASE_URL": "http://localhost:4000/v1",
    "OPENAI_API_KEY": "<LITELLM_MASTER_KEY> | <LITELLM_VIRTUAL_KEY>"
 }
in the ~/.claude/settings.json file in order for claude to reroute it's traffic. 