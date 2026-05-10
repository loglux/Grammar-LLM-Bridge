# Grammar-LLM-Bridge

> LanguageTool-compatible FastAPI server that bridges LT clients (Obsidian plugins, browser extensions, etc.) to **any OpenAI-compatible LLM backend** for grammar and spell checking.

[![CI](https://github.com/loglux/Grammar-LLM-Bridge/actions/workflows/ci.yml/badge.svg)](https://github.com/loglux/Grammar-LLM-Bridge/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](./LICENSE)

Talks the `/v2/check` LanguageTool API on one side and OpenAI-compatible chat-completions on the other (OpenAI, DeepSeek, OpenRouter, Anthropic via OpenRouter, Ollama, ...). Drop it in front of any LT plugin and get LLM-quality grammar checks against the model of your choice.

Tested with the two main Obsidian LT plugins:

- [`Clemens-E/obsidian-languagetool-plugin`](https://github.com/Clemens-E/obsidian-languagetool-plugin) — the original (maintenance mode).
- [`wrenger/obsidian-languagetool`](https://github.com/wrenger/obsidian-languagetool) — a more active fork.

If you want a build that includes a pending fix for the long-standing auto-check
"underlines may not move correctly when typing" race condition, see
[`loglux/obsidian-languagetool`](https://github.com/loglux/obsidian-languagetool) —
a fork of `wrenger` with the fix applied (also submitted upstream as
[wrenger #56](https://github.com/wrenger/obsidian-languagetool/pull/56) and
[Clemens-E #144](https://github.com/Clemens-E/obsidian-languagetool-plugin/pull/144)).

All three send `apiKey` and `username` in the request body (form-urlencoded); the Bridge's auth middleware understands that flow.

## Quick start

### 1. Clone and configure

```bash
git clone https://github.com/loglux/Grammar-LLM-Bridge.git
cd Grammar-LLM-Bridge
cp .env.example deploy/load-balancer/.env.bridge
$EDITOR deploy/load-balancer/.env.bridge       # set OPENAI_API_KEY etc.
```

`.env.example` documents every variable, including aggressive-chunking options that reduce context-induced false positives.

### 2. Build and run

Production stack (nginx load-balancer + two app replicas, port `8081`):

```bash
make build         # docker build -t grammar-llm-bridge:latest .
make up            # docker compose up -d
make logs-01       # tail one replica's logs
```

Single dev instance on port `9019` (handy for the browser test UI below):

```bash
make up-dev
make logs-dev
```

### 3. Point your client at it

For an Obsidian LT plugin, set **Server URL** to:

- `http://localhost:8081/v2/check` (LB) or
- `http://localhost:9019/v2/check` (dev).

`grammar-checker.html` in the repo root is a self-contained browser test UI — open it directly in a browser, no build step required.

## Configuration knobs

All via env vars (see `.env.example` for the canonical list):

| Variable | Purpose |
|---|---|
| `OPENAI_API_KEY` / `OPENAI_BASE_URL` / `LLM_MODEL` | Backend selection (any OpenAI-compatible API). |
| `GRAMMAR_ONLY` | If `true`, suppresses style/wordiness suggestions. |
| `TYPOGRAPHY_CHECK` | Include typographic issues. |
| `LLM_CHUNKING` / `LLM_CHUNK_SIZE` / `LLM_CHUNK_THRESHOLD` | Split long inputs into chunks (each its own LLM call). |
| `LLM_CHUNK_STRATEGY` | `paragraph` (legacy) or `recursive` (LaTeX-safe, splits inside paragraphs by sentence to reduce false positives). |
| `LLM_TIMEOUT` | Per-request timeout in seconds. |

## Layout

| Path | Purpose |
|---|---|
| `app/` | Modular FastAPI package; entrypoint `app.main:app`. |
| `deploy/load-balancer/` | Production Docker Compose stack (nginx + 2 replicas + shared SQLite). |
| `docs/` | Architecture, auth, prompt rules, level modes. |
| `docs/research/` | Background notes and design discussions. |
| `docs/qa/` | QA-observed model-behaviour notes. |
| `qa-results/quality/` | Curated gold suites and quality runners. |
| `qa-results/ad-hoc/` | Ad-hoc tools (`run_samples.py`, `analyze_last_run.py`) and sample texts. |
| `tests/unit/` | Unit tests for the bridge (chunking, masking, mapping). |
| `Makefile` | Build / run / logs / smoke / quality. |
| `grammar-checker.html` | Self-contained browser test UI. |

## Development

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
pip install ruff pytest

ruff check app/ tests/       # lint
pytest tests/ -v             # unit tests (currently 21)
```

CI runs the same `ruff` + `pytest` on every push to `master` against Python 3.11 and 3.12 — see [`.github/workflows/ci.yml`](./.github/workflows/ci.yml).

## How it works (one paragraph)

The LT plugin sends an annotated text (text + markup parts) to `/v2/check`. The Bridge extracts a *logical* text without markup, builds a position map, optionally splits the logical text into chunks, and asks the configured LLM to find grammar errors. The LLM's suggestions come back with offsets in logical-text space; the Bridge maps them back to the original markup-aware offsets the plugin expects, deduplicates overlapping spans, and returns an LT-compatible response. LaTeX math blocks are detected and protected so they aren't underlined and aren't cut in the middle by the chunker.

## Privacy

Your text is sent to whichever LLM provider you configure. If you'd rather keep everything on your machine, point the Bridge at a local Ollama (or similar) instance — same `OPENAI_BASE_URL` / `LLM_MODEL` pair, no external traffic.

## License

[MIT](./LICENSE) © loglux. Forks, PRs, and issue reports welcome.
