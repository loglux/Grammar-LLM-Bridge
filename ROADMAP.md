# Roadmap

Not a release schedule — a public backlog of things we'd like to improve next. Roughly grouped by area, no fixed dates.

## Language support

The Bridge advertises multiple languages via `GET /v2/languages` and forwards whichever `language` code the client sends to the LLM. The plumbing is there, but the prompt is English-centric.

- [ ] **Per-language prompt blocks.** Today `app/prompts.py` builds one prompt from English-only guard blocks (SVA, article rules, ESL hints). These aren't a starting point for other languages — each language needs its own native set of rules (Russian has no articles, German has cases and compounds, Spanish has ser/estar and accents, etc.).

  Planned layout (replaces the current single file):

  ```
  app/prompts/
  ├── __init__.py        # exports get_prompt(language, mode) dispatcher
  ├── common.py          # language-agnostic blocks: SYSTEM_INTRO, MODE_BLOCK,
  │                      # output-format rules, LaTeX/markdown guards
  ├── en.py              # English-specific: SVA, articles, ESL, confusables
  ├── ru.py              # Russian: падежи, согласование, частые ошибки
  ├── de.py              # German: cases, articles, compound-word splits
  ├── fr.py              # French: accords, élision, accents
  └── es.py              # Spanish: ser/estar, accents, agreement
  ```

  Dispatcher contract (`app/prompts/__init__.py`):

  ```python
  def get_prompt(language: str, mode: str) -> str:
      """Compose the system prompt for the given LT language code and mode.

      Strategy:
      1. Normalise `language` to a 2-letter root (en-GB → en, ru-RU → ru).
      2. Start with `common.SYSTEM_INTRO + common.MODE_BLOCK(mode)`.
      3. If a `app/prompts/<lang>.py` module exists, append its blocks.
      4. If not, fall back to `en` blocks and log a warning.
      """
  ```

  Each language module exports a fixed surface (e.g. `SVA_BLOCK`, `ARTICLE_BLOCK`, `EXTRA_GUARDS`) so the dispatcher can assemble them uniformly.

  Level modes (`default` / `picky`) are **orthogonal to language**: the `MODE_BLOCK` lives in `common.py` and applies universally ("be strict" vs "be lenient" reads the same across languages). Individual language modules may export an optional `PICKY_EXTRA` block for language-specific picky-only rules (e.g. Russian punctuation nuances) that the dispatcher appends only when `mode=picky`.

  Tests live under `tests/unit/prompts/test_<lang>.py`, plus a small per-language gold suite under `qa-results/quality/<lang>/`.
- [ ] **Auto-detection for `language=auto`.** Research on candidate detectors (fastText / langid / cld3 / langdetect) is in [`docs/research/QA_LANGUAGE_DETECTION.md`](./docs/research/QA_LANGUAGE_DETECTION.md). Once a detector is in, wire it to fill in `language` when the client sends `auto`, and feed the result into prompt-block selection.
- [ ] **Language-specific gold suites.** `qa-results/quality/` currently holds English suites; add small Russian/German/French sets so we can compare model behaviour per language.

## Prompts & rules

- [ ] **Style / toneTags wiring.** Templates exist in [`docs/style_prompt_blocks.md`](./docs/style_prompt_blocks.md). Plan: accept `toneTags` / `goal` from the client, expand to the matching block, append below the core grammar guards.
- [ ] **Multi-variant replacements.** LT supports `replacements: [{value: ...}, ...]`; the model sometimes packs multiple options into one string. Plan: have prompts request 1–3 variants explicitly, parse the array, and surface all variants to the client.
- [ ] **Better SVA and confusable handling.** SVA guard reduced false negatives on DeepSeek (see `docs/sva_prompt_update.md`) but OpenAI/Claude remain noisier. Plan: tighten with negative examples and a per-model post-filter.

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
