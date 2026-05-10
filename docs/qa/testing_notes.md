# Testing notes

- Runner: `qa-results/quality/run_quality.py`
  - Args: `--suite core|smoke|custom`, `--endpoint`, `--gold`, `--timeout`
  - Outputs per-case request/response, `report.txt`, and `run_meta.json` (endpoint, suite, gold path, env).
  - Latency: logs per-case average/max (ms) at the end.
  - Default timeout: 60s per request.
- Suites:
  - `gold_core.json`: main 23-case gold set (copied from `qa_gold.json`).
  - `gold_smoke.json`: 5 short cases (SVA, spelling, inline/block math, punctuation).
  - `qa_gold.json`: legacy core if needed.
  - `latex`/`punct`/`negative`: to be added separately if needed.
- Local automation script (not in repo): `run_model_quality.sh`
  - Usage: `OPENAI_API_KEY=... ./run_model_quality.sh <model> [port] [base_url] [api_key]`
  - Steps: start temp container with model, run `run_quality.py` against `http://localhost:<port>/v2/check`, save results to `qa-results/quality/run-<timestamp>`, then remove container.
  - Defaults: port 9040, base_url `https://api.openai.com/v1`, api_key from env if not passed.
- Recent best models (strict P/R):
  - gpt-4.1: 100 / 96.43
  - gpt-4.1-mini: 96.15 / 92.59
  - deepseek-chat: 100 / 89.66
  - claude-sonnet-4.5: 96.30 / 89.66
  - Others (llama/gemma/4o-mini/gpt-5-mini) performed significantly worse; 405b/120b timed out or returned invalid JSON.

