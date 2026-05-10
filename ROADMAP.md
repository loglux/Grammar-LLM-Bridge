# Roadmap

Not a release schedule — a public backlog of things we'd like to improve next. Roughly grouped by area, no fixed dates.

## Prompts, languages, modes

All prompt-level changes (per-language modules, `language=auto` detection, style/toneTags wiring, multi-variant replacements, SVA tuning) are designed and tracked in [`docs/prompt_rules.md`](./docs/prompt_rules.md#future--planned), kept next to the current firewall description so design and roadmap don't drift apart.

One related testing item is parked here:

- [ ] **Language-specific gold suites.** `qa-results/quality/` currently holds English suites; add small Russian/German/French sets so we can compare model behaviour per language. (Companion to per-language prompt modules in `prompt_rules.md`.)

## Testing

- [ ] **Unit tests for `app/error_finder.py`.** Currently only chunking, masking, and extract/mapping are covered (21 tests). The error-finder owns several heuristics (article guards, punctuation skips, token-boundary checks) — high-value to test in isolation.
- [ ] **Unit tests for `app/position_mapper.py`.** Logical → original → UTF-16 mapping is one of the trickiest parts; integration smoke tests pass it through, but unit tests would catch regressions earlier.
- [ ] **End-to-end test in real Obsidian** for the auto-check race-condition fix in our plugin fork. The unit tests in `loglux/obsidian-languagetool` cover the freshness check in isolation; a recorded mouse-and-keyboard run in Obsidian against a slow Bridge would confirm the fix prevents stale underlines visually.

## Providers & deployment

- [ ] **Native Anthropic API support.** Currently we reach Claude via OpenRouter. Direct `anthropic` SDK would save ~20% per million tokens and reduce a hop. Plan documented in `local/LOCAL_NOTES.md` (Future section).
- [ ] **Optional Redis-backed rate limiting.** The in-memory limiter in `app/auth/rate_limiter.py` resets on container restart and isn't shared between replicas. Plan: pluggable backend so production deployments can opt into Redis.
- [ ] **Optional metrics.** Prometheus endpoint with per-model latency / token usage / FP-rate (when annotated).

## Repo hygiene

- [ ] **Split `app/text_processing.py`** (currently 482 lines mixing extract / mask / sentence-split / two chunkers / retry helper). When the next module joins, split into `app/text/extract.py`, `app/text/masking.py`, `app/chunking.py`.
- [ ] **CONTRIBUTING.md** once the first external contributor lands — keep PR conventions, dev setup, commit-message style in one place.
