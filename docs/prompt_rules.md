# Prompt Rules

## Design: prompt as a semantic firewall

The system prompt is built from blocks in `app/prompts.py` that fall into two roles, deliberately ordered:

1. **Forbid / Guard** — narrow the model's behaviour. SVA guard, "no style/quote rewrites", "skip inside `$…$`", minimal-fragment discipline. These reduce noise.
2. **Allow / Require** — explicitly re-open a few high-value error classes that a strict reading of the forbid block would suppress (e.g. missing determiners before singular countable nouns).

We treat this pattern as a *semantic firewall*: by default the model is restrained, then specific "ports" are opened for the error types we actually want. New rules should be added in the same shape — a new forbid block needs at least an allow companion if it would block a useful class of corrections, and a new allow block should be narrow enough not to re-introduce style/tone noise.

`MODE_BLOCK` (level=default/picky) tunes how strict the firewall is — it doesn't replace it, just adjusts sensitivity. See [`LEVEL_MODES.md`](./LEVEL_MODES.md) for the per-mode behaviour matrix.

The lists below are the current state of the firewall. Update them whenever a prompt block in `app/prompts.py` changes.

## Forbid / Guard
- **Style/quotes:** No style/tone rewrites. Ignore straight vs curly quotes/apostrophes unless it is a grammar error; do not switch quote styles.
- **SVA guard:** Flag only the incorrect verb; do not change a correct “is/are” when the true subject is singular (e.g., “The list of items is…” is correct).
- **LaTeX:** Skip inside `$...$` / `$$...$$`; punctuation/capitalization after formulas is part of the same sentence. Inline `$x$` treated as variables; do not suggest caps after formulas.
- **Span discipline:** Use minimal fragments; no overlaps/duplicates; keep error within the same sentence.

## Allow / Require
- **Scope:** Grammar, spelling, punctuation, collocations/word choice, articles.
- **Articles:** Missing determiner before singular countable nouns must be reported. Determiners include a/an, the, this/that/these/those, my/your/his/her/its/our/their, some/any, each/every, no, another, numbers, possessives (John’s).
- **Articles – do NOT report:** Proper nouns, plural generic nouns, mass/uncountable nouns, fixed expressions (go to school, at home, in bed, by car, at work).
- **Article replacements constraint:** Preserve meaning; no new semantics; no possessives unless explicit; prefer neutral a/an or the.
- **Replacements format:** Always an array, 1–5 options, ordered by quality; keep sentence boundaries intact.
- **Output format:** Top-level JSON array only; each item must have message, error_text (exact substring), replacements (array ≥1).

## Notes
- System + user split is required (system = instructions, user = Language + Text).
- When adding new “allow” rules, keep them narrow to avoid noise. Maintain the forbid/allow list here and in prompt updates.

## Future / Planned

These extend the firewall in the same forbid/allow shape rather than replacing it. Ordered roughly by impact.

### Per-language prompt modules

**Scaffolding: done.** `app/prompts.py` was split into a package (`app/prompts/`) with `common.py` (language-neutral blocks), `en.py` (English-specific SVA / articles / confusables), and an `__init__.py` exposing `get_prompt(language, level)` plus `GRAMMAR_SCHEMA`. The dispatcher normalises locales (`en-GB` → `en`, case-insensitive) and falls back to English with a warning for unknown languages. The three LLM providers (`deepseek.py`, `openai.py`, `fallback.py`) now call `get_prompt(language, level)` per request. Behaviour for current callers is unchanged byte-for-byte. Design and per-commit history live in [`research/prompts_modular_refactor.md`](./research/prompts_modular_refactor.md).

Current layout:

```
app/prompts/
├── __init__.py        # get_prompt(language, level) dispatcher
├── common.py          # SYSTEM_INTRO, MODE_BLOCK, output/format/critical
│                      # blocks, LaTeX guards, GRAMMAR_SCHEMA
└── en.py              # English: SVA, articles, confusables (BLOCKS list)
```

**Per-language content: pending.** Adding `ru.py`, `de.py`, `fr.py`, `es.py`, etc. is now a one-file change per language: create `app/prompts/<lang>.py` exporting a `BLOCKS = [...]` list, then register one row in `_LANGUAGE_MODULES` in `__init__.py`. Each new language should ship with:

- a per-language gold suite under `qa-results/quality/<lang>/`,
- focused unit tests if the module adds non-trivial logic (most won't — pure block lists need no extra unit tests beyond the dispatcher's).

Level modes (`default`/`picky`) are orthogonal to language: `MODE_BLOCK` lives in `common.py` and applies universally. A language module may export an optional `PICKY_EXTRA` block for picky-only additions; the dispatcher will be extended to consume it when the first language needs it.

### `language=auto` auto-detection

Research on candidate detectors (fastText / langid / cld3 / langdetect) is in [`research/QA_LANGUAGE_DETECTION.md`](./research/QA_LANGUAGE_DETECTION.md). Once a detector is in, wire it to fill in `language` when the client sends `auto`, then feed the result into the dispatcher above.

### Style / toneTags wiring

Templates exist in [`style_prompt_blocks.md`](./style_prompt_blocks.md): accept `toneTags` / `goal` from the client, expand to the matching block, append below the core grammar guards. Treat as another "allow" overlay on top of the firewall.

### Multi-variant replacements

LT supports `replacements: [{value: ...}, ...]`. The model sometimes packs multiple options into one string. Plan: have prompts request 1–3 variants explicitly, parse the array, and surface all variants to the client.

### Better SVA and confusable handling

The SVA guard reduced false negatives on DeepSeek (see [`research/sva_prompt_block_ab.md`](./research/sva_prompt_block_ab.md)) but OpenAI/Claude remain noisier. Plan: tighten with negative examples and a per-model post-filter.
