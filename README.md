# Grammar-LLM-Bridge

LanguageTool-compatible FastAPI server bridging LT clients (Obsidian, etc.) to OpenAI-compatible LLM backends for grammar checking.

Tested with both popular Obsidian LT plugins:

- [`Clemens-E/obsidian-languagetool-plugin`](https://github.com/Clemens-E/obsidian-languagetool-plugin) — the original.
- [`wrenger/obsidian-languagetool`](https://github.com/wrenger/obsidian-languagetool) — a fork with its own markdown handling.

Both send `apiKey` and `username` in the request body (form-urlencoded); the Bridge's auth middleware accepts that flow.

For local QA / operational notes (not in this repo): see `local/LOCAL_NOTES.md` and the `local/` directory.

## Quick start

```bash
source venv/bin/activate
make help
```

Common targets: `make build`, `make up` / `up-dev`, `make logs-01` / `logs-dev`, `make smoke`, `make quality MODEL=…`. Run `make help` for the full list.

## Layout

| Path | Purpose |
|---|---|
| `app/` | Modular FastAPI package; entrypoint `app.main:app` |
| `deploy/load-balancer/` | Production stack (nginx + 2 replicas + shared SQLite) |
| `docs/` | Architecture, auth, prompt rules, level modes |
| `docs/research/` | Background notes and design discussions |
| `docs/qa/` | QA-observed model behaviour notes |
| `qa-results/quality/` | Curated gold suites and quality runners |
| `qa-results/ad-hoc/` | Sample inputs and ad-hoc tools (`run_samples.py`, `analyze_last_run.py`) |
| `Makefile` | Build / run / logs / smoke / quality |
| `local/` | Local-only notes (gitignored) |

## Endpoints

- Prod (load-balanced, 2 replicas): `http://localhost:8081/v2/check`
- Dev profile (single instance): `http://localhost:9019/v2/check`

## Browser test UI

`grammar-checker.html` is a self-contained, single-file web UI for sending text to any LanguageTool-compatible `/v2/check` endpoint and viewing returned matches. No build step — just open the file in a browser.

The default backend URL is `http://localhost:9019/v2/check` (Grammar-LLM-Bridge dev profile). You can point it at any other LT-compatible API by editing the field at the top of the page. A backend **is** required — the page is a thin client and doesn't perform any checking on its own.

```bash
make up-dev          # start the dev backend
xdg-open grammar-checker.html   # or open it any way you like
```

## Configuration

Runtime configuration is injected via `deploy/load-balancer/.env.bridge` (gitignored, contains the API key and model selection). Never bake secrets into the Dockerfile or commit `.env*` files.

## License

[MIT](./LICENSE) © loglux.
