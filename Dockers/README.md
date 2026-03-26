# LiteLLM Proxy — Docker Stack

A minimal Docker Compose stack that runs a [LiteLLM](https://docs.litellm.ai/) proxy backed by PostgreSQL and Redis. It gives you a single `http://localhost:4000` endpoint that speaks the OpenAI API format while routing requests to Anthropic, Google Gemini, OpenAI, or any host-local runtime (Ollama, LM Studio, etc.).

## Prerequisites

- Docker Engine 24+ and Docker Compose v2
- At least one upstream provider API key (Anthropic, OpenAI, or Gemini)

## Quick Start

```bash
# 1. Clone and enter the directory
cd Dockers

# 2. Create your .env from the template
cp .env.example .env

# 3. Fill in real secrets in .env (see Environment Variables below)

# 4. Start the stack
docker compose up -d

# 5. Verify all services are healthy
docker compose ps
```

Once healthy, the proxy is available at **http://localhost:4000** and the dashboard at **http://localhost:4000/ui**.

## Architecture

```
                    ┌─────────────────────────┐
                    │      LiteLLM Proxy       │
                    │   localhost:4000          │
                    │   (ghcr.io/berriai/       │
                    │    litellm:main-stable)   │
                    └────┬──────────┬──────────┘
                         │          │
            ┌────────────┘          └────────────┐
            ▼                                    ▼
   ┌─────────────────┐                ┌─────────────────┐
   │    PostgreSQL    │                │      Redis      │
   │  127.0.0.1:5432 │                │ 127.0.0.1:6379  │
   │  (postgres:16)  │                │  (redis:7)      │
   └─────────────────┘                └─────────────────┘
```

**Startup order:** Postgres and Redis must pass their healthchecks before LiteLLM starts.

All three services share the `litellm-net` bridge network and communicate by service name. Postgres and Redis bind to `127.0.0.1` only; LiteLLM binds to all interfaces.

### Service Endpoints

| Service    | URL / Address         | Notes                                    |
|------------|-----------------------|------------------------------------------|
| LiteLLM UI | http://localhost:4000/ui | Authenticate with `LITELLM_MASTER_KEY` |
| LiteLLM API | http://localhost:4000  | Bearer token = `LITELLM_MASTER_KEY`    |
| PostgreSQL | 127.0.0.1:5432        | Local only                               |
| Redis      | 127.0.0.1:6379        | Local only                               |

## Configuration

### File Map

| File                  | Purpose                                        |
|-----------------------|------------------------------------------------|
| `docker-compose.yaml` | Service definitions, networking, healthchecks  |
| `litellm-config.yaml` | Model list, DB/cache settings, general options |
| `.env`                | Local secrets and runtime values               |
| `.env.example`        | Safe placeholder template (committed to repo)  |

### Environment Variables

Copy `.env.example` to `.env` and fill in real values. The stack will not start without the required variables.

**Required:**

| Variable              | Purpose                                                                 |
|-----------------------|-------------------------------------------------------------------------|
| `LITELLM_MASTER_KEY`  | Admin key for the proxy UI and API. Must start with `sk-`.             |
| `LITELLM_SALT_KEY`    | Encrypts provider API keys stored in Postgres. **Set once, never change.** |
| `POSTGRES_USER`       | Postgres username                                                       |
| `POSTGRES_DB`         | Postgres database name                                                  |
| `POSTGRES_PASSWORD`   | Postgres password                                                       |
| `REDIS_PASSWORD`      | Redis auth password                                                     |

**Optional:**

| Variable          | Default         | Purpose                            |
|-------------------|-----------------|------------------------------------|
| `GEMINI_API_KEY`  | *(empty)*       | Google Gemini provider key         |
| `OPENAI_API_KEY`  | *(empty)*       | OpenAI provider key                |
| `TZ`              | `Europe/Berlin` | Container timezone                 |

> **Warning — `LITELLM_SALT_KEY` is immutable.**
> Once LiteLLM has stored encrypted provider keys in Postgres, changing `LITELLM_SALT_KEY` renders those saved secrets unreadable. Pick a strong value on first run and keep it permanently.

## Pre-Configured Models

Models are defined in `litellm-config.yaml`. The stack ships with:

| Model Name                     | Provider  | Max Tokens | Timeout |
|--------------------------------|-----------|------------|---------|
| `claude-opus-4-6`             | Anthropic | 128,000    | 600s    |
| `claude-sonnet-4-6`           | Anthropic | 64,000     | 300s    |
| `claude-haiku-4-5-20251001`   | Anthropic | 64,000     | 120s    |
| `gemini-3.1-pro-preview`      | Gemini    | —          | —       |
| `gemini-3.1-flash-lite-preview` | Gemini  | —          | —       |
| `gpt-5.4`                     | OpenAI    | 128,000    | —       |
| `gpt-5-mini`                  | OpenAI    | 128,000    | —       |
| `gpt-5-nano`                  | OpenAI    | 128,000    | —       |

### Adding a Model

Add an entry under `model_list` in `litellm-config.yaml`:

```yaml
- model_name: my-new-model
  litellm_params:
    model: provider/model-id
    api_key: os.environ/MY_PROVIDER_KEY   # or omit for header forwarding
    max_tokens: 64000
```

Then restart:

```bash
docker compose restart litellm
```

## Connecting Claude Code

https://docs.litellm.ai/docs/tutorials/claude_code_byok
https://docs.litellm.ai/docs/proxy/forward_client_headers

You can generate the Virtual Key from the Litellm UI dashboard as well.

To route Claude Code traffic through the LiteLLM proxy, add the following `env` block to `~/.claude/settings.json` or add export them in the shell file (zshrc or bashrc)

```json
{
  "env": {
    "ANTHROPIC_BASE_URL": "http://localhost:4000",
    "ANTHROPIC_CUSTOM_HEADERS": "x-litellm-api-key: Bearer <LITELLM_MASTER_KEY or VIRTUAL_KEY>",
    "OPENAI_BASE_URL": "http://localhost:4000/v1",
    "OPENAI_API_KEY": "<LITELLM_MASTER_KEY or VIRTUAL_KEY>"
  }
}
```


Replace `<LITELLM_MASTER_KEY or VIRTUAL_KEY>` with the value of `LITELLM_MASTER_KEY` from your `.env` file, or a virtual key generated through the LiteLLM UI.

### How It Works

- `ANTHROPIC_BASE_URL` redirects all Anthropic SDK calls to the proxy.
- `ANTHROPIC_CUSTOM_HEADERS` injects the `x-litellm-api-key` header so LiteLLM authenticates the request.
- `forward_client_headers_to_llm_api: true` in `litellm-config.yaml` passes Anthropic-specific headers (beta features, etc.) through to the upstream API.
- The Anthropic models in this config have **no hardcoded `api_key`** — they rely on the client forwarding its own key via the `x-api-key` header. This means your Anthropic API key travels with each request from Claude Code through the proxy to Anthropic.
- `OPENAI_BASE_URL` and `OPENAI_API_KEY` allow any OpenAI-compatible tooling in Claude Code to also route through the proxy.

## Connecting Other Services

### OpenAI-Compatible Clients (Cursor, Continue, Cline, etc.)

Any tool that supports a custom OpenAI base URL can point to the proxy:

| Setting         | Value                         |
|-----------------|-------------------------------|
| Base URL        | `http://localhost:4000/v1`    |
| API Key         | Your `LITELLM_VIRTUAL_KEY`    |
| Model           | Any model name from the table above (e.g. `claude-sonnet-4-6`) |

### Host-Local Models (Ollama, LM Studio)

The `extra_hosts: host.docker.internal:host-gateway` directive lets LiteLLM reach services running on your host machine. To add a local Ollama model:

```yaml
- model_name: llama3
  litellm_params:
    model: ollama/llama3
    api_base: http://host.docker.internal:11434
```

### Direct API Calls

```bash
# Chat completion
curl http://localhost:4000/v1/chat/completions \
  -H "Authorization: Bearer $LITELLM_MASTER_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "claude-sonnet-4-6",
    "messages": [{"role": "user", "content": "Hello!"}]
  }'

# List available models
curl http://localhost:4000/v1/models \
  -H "Authorization: Bearer $LITELLM_MASTER_KEY"

# Health check
curl http://localhost:4000/health
```

## Common Commands

```bash
# Validate the rendered compose file
docker compose config

# Start the stack
docker compose up -d

# Stop without removing data
docker compose down

# Stop and remove all persistent data (volumes)
docker compose down -v

# Restart LiteLLM after config changes
docker compose restart litellm

# Follow logs
docker compose logs -f litellm
docker compose logs -f postgres
docker compose logs -f redis

# Check service health
docker compose ps
```

## Troubleshooting

### LiteLLM fails to start or stays "unhealthy"

Check that Postgres and Redis are healthy first:

```bash
docker compose ps postgres redis
docker compose logs litellm
```


### "Connection refused" from Claude Code

1. Verify the stack is running: `docker compose ps`
2. Confirm `ANTHROPIC_BASE_URL` in `~/.claude/settings.json` is `http://localhost:4000` (not `https`).
3. Confirm the `x-litellm-api-key` header value matches your `LITELLM_MASTER_KEY`.
4. /login inside the Claude Code

### Stored provider keys become unreadable

You changed `LITELLM_SALT_KEY` after provider keys were already encrypted. The only fix is to reset the database and re-add keys:

```bash
docker compose down -v
docker compose up -d
```

### Redis cache issues

Redis is configured as an ephemeral LRU cache with persistence disabled. Restarting Redis clears the cache — this is expected and harmless.
