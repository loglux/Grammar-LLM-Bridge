# Load Balancer Setup (Docker Compose + Nginx)

Current stack matches `docker-compose.yml` in this folder. Service names and ports:
- `grammar-llm-01`, `grammar-llm-02`: two `grammar-llm-bridge:latest` workers (env from `.env.bridge`, no host ports exposed).
- `grammar-llm-balancer`: nginx listening on host `8081` → proxies to the two workers (config in `lb.conf`).
- `grammar-llm-dev` (optional, profile `dev`): single worker with host port `9019:8000` for local/direct testing.
- `lb.conf` is the active nginx config. `default.conf` is intentionally empty/unused (keeps the default site disabled).

## Prepare env
- `.env.bridge` (not committed) supplies backend secrets and flags. Copy the template at the repo root and edit:
  ```bash
  cp ../../.env.example .env.bridge
  $EDITOR .env.bridge   # set OPENAI_API_KEY, OPENAI_BASE_URL, LLM_MODEL, etc.
  ```
  [`.env.example`](../../.env.example) documents every variable (backend selection, chunking strategy, timeouts). Minimum to start: `OPENAI_API_KEY` + `OPENAI_BASE_URL` + `LLM_MODEL`.

## Run / restart
From `deploy/load-balancer/` in the repo root:
```
# Stop existing stack (removes old containers so names don't collide)
docker compose down

# Start balancer + two workers
docker compose up -d          # nginx on 8081

# Start dev node (optional, maps 9019:8000)
docker compose --profile dev up -d grammar-llm-dev
```

## Status & quick tests
```
docker ps --format 'table {{.Names}}\t{{.Status}}\t{{.Ports}}' | grep grammar-llm
curl -s -w 'status:%{http_code} time:%{time_total}\n' http://localhost:8081/v2/info
curl -s -H 'Content-Type: application/json' -d '{"text":"This are tests"}' http://localhost:8081/v2/check
```
Expected host endpoints:
- Load-balanced: `http://localhost:8081/v2/check` (and `/v2/info`, `/health`).
- Dev profile (if enabled): `http://localhost:9019/v2/check`.

## Notes
- Nginx `proxy_read_timeout` is 130s (>= `LLM_TIMEOUT` + margin). Adjust both if you change `LLM_TIMEOUT`.
- Keep `.env.bridge` out of version control.
- To add more workers, duplicate `grammar-llm-01/02` in `docker-compose.yml` and list them in `lb.conf` upstream.
