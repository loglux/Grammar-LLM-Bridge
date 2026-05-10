# Grammar-LLM-Bridge

[![CI](https://github.com/loglux/Grammar-LLM-Bridge/actions/workflows/ci.yml/badge.svg)](https://github.com/loglux/Grammar-LLM-Bridge/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](./LICENSE)

A FastAPI server that speaks the `/v2/check` LanguageTool API on one side and OpenAI-compatible chat-completions on the other (OpenAI, DeepSeek, OpenRouter, Anthropic via OpenRouter, Ollama, ...). Drop it in front of any LT client — Obsidian plugin, browser extension, custom integration — and get LLM-quality grammar checks against the model of your choice.

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

## Production topology

The `deploy/load-balancer/` stack runs three containers behind one host port:

```
                ┌──────────────────────────────┐
host :8081 ─────▶ grammar-llm-balancer (nginx) │   round-robin
                └──────┬──────────────┬────────┘
                       │              │
                       ▼              ▼
              grammar-llm-01    grammar-llm-02
               (FastAPI/        (FastAPI/
                uvicorn 4w)      uvicorn 4w)
                       │              │
                       └─────┬────────┘
                             ▼
                  shared SQLite (bind mount `./data`,
                  DATABASE_URL=sqlite+aiosqlite:///…)
```

- `nginx` listens on **`:8081`** and round-robins between the two replicas (no host ports on the replicas themselves — they are reachable only inside the docker network).
- Each replica is `grammar-llm-bridge:latest` running `uvicorn app.main:app --workers 4`.
- A separate `grammar-llm-dev` profile exposes a single replica on **`:9019`** for local testing (`make up-dev`).
- LLM API calls are stateless; auth state and rate-limiter counters live in the shared SQLite file so both replicas see the same `apiKey` records.

For details (network config, fixed IPs, capacity planning) see:

- [`deploy/load-balancer/LOAD_BALANCER_SETUP.md`](./deploy/load-balancer/LOAD_BALANCER_SETUP.md) — concrete setup steps.
- [`deploy/load-balancer/NETWORK_NOTES.md`](./deploy/load-balancer/NETWORK_NOTES.md) — `extra_hosts` workaround, DNS notes.
- [`deploy/load-balancer/CAPACITY.en-GB.md`](./deploy/load-balancer/CAPACITY.en-GB.md) — throughput math and recommended limits.

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

## How it works

The LT plugin sends an annotated text (text + markup parts) to `/v2/check`. The Bridge extracts a *logical* text without markup, builds a position map, optionally splits the logical text into chunks, and asks the configured LLM to find grammar errors. The LLM's suggestions come back with offsets in logical-text space; the Bridge maps them back to the original markup-aware offsets the plugin expects, deduplicates overlapping spans, and returns an LT-compatible response. LaTeX math blocks are detected and protected so they aren't underlined and aren't cut in the middle by the chunker.

## Languages

This is an **experimental** project tuned around English (en-GB / en-US is what the test suite covers). Mechanically the Bridge is language-agnostic — it forwards whatever `language` code the client sends (`ru-RU`, `de-DE`, `fr-FR`, ...) to the LLM, and modern multilingual models (DeepSeek, GPT-4.x, Claude, ...) will return grammar suggestions for that language.

Two caveats — what is and isn't there:

- **Language parameter is plumbed through**: `GET /v2/languages` advertises en-US/GB/AU, ru-RU, de-DE, fr-FR, es-ES, and `auto`. The `language` field from the client is passed into the LLM prompt verbatim.
- **System prompt is English-centric**: the rule blocks in `app/prompts.py` (subject–verb agreement, article rules, ESL hints) are written for English. On other languages they don't apply or produce a different false-positive profile.
- **No real auto-detection yet**: sending `language=auto` just forwards the string to the LLM, which usually figures the language out on its own but without confidence guarantees. A comparison of candidate detectors (fastText/langid/cld3/langdetect) for a future implementation lives in [`docs/research/QA_LANGUAGE_DETECTION.md`](./docs/research/QA_LANGUAGE_DETECTION.md).

To get production-quality results in another language you'll likely want to:

1. Adapt the prompt blocks for that language (or add a per-language overlay — [`docs/prompt_rules.md`](./docs/prompt_rules.md) documents the forbid/allow structure).
2. Run a small gold-suite (`qa-results/quality/`) for the target language to compare model outputs.

See also [`docs/LEVEL_MODES.md`](./docs/LEVEL_MODES.md) for how `picky`/`default` modes inherit rules, and [`docs/style_prompt_blocks.md`](./docs/style_prompt_blocks.md) for style/toneTags presets.

A concrete plan for splitting prompts into per-language modules (`app/prompts/en.py`, `ru.py`, `de.py`, ...) with a `get_prompt(language, mode)` dispatcher lives in [`ROADMAP.md`](./ROADMAP.md#language-support).

## Privacy

Your text is sent to whichever LLM provider you configure. If you'd rather keep everything on your machine, point the Bridge at a local Ollama (or similar) instance — same `OPENAI_BASE_URL` / `LLM_MODEL` pair, no external traffic.

## License

[MIT](./LICENSE) © loglux. Forks, PRs, and issue reports welcome.
