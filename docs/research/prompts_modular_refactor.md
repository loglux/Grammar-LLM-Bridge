# Prompts: modular refactor

Status: **planned** (no commits yet). Tracked here as a working doc; the canonical short summary lives in [`prompt_rules.md` → Future / Planned](../prompt_rules.md#per-language-prompt-modules).

## Why

`app/prompts.py` is a single file (153 lines) that builds one global `SYSTEM_MESSAGE` from 13 blocks. All blocks are English-tuned: SVA examples in English (*"horses runs fast"*), full article-rules section, English ESL hints, confusable-words heuristic. The same prompt is sent to the LLM for any value of `language` — only one line `Language: <code>` is appended to the user message.

This is fine for English-only use, but it has two concrete problems:

1. **False positives on languages without articles** (e.g. Russian). The model gets a long, confident "ARTICLES — TRIGGER" block ordering it to report missing determiners. Even if `Language: ru` is mentioned in the user message, the system block is more salient and the model often flags Russian sentences for "missing articles".
2. **No place to add language-specific rules**. To handle Russian падежи, German cases, French accents, we would have to mix all of them into one ever-growing file. The blocks would start contradicting each other or relying on the model to pick the right one based on a hint — both fragile.

We already have three orthogonal axes in the API:

- **Language** (`language=en-GB|ru|...`) — wired through but only affects one user-message line.
- **Level** (`level=default|picky`) — wired through *and* affects the prompt via `MODE_BLOCK`. Works.
- **Style** (`goal`/`toneTags`) — not accepted by the API. Block templates exist in [`style_prompt_blocks.md`](../style_prompt_blocks.md), not wired.

This refactor only touches the **language axis** scaffolding. It does not add any new language; it does not touch level or style.

## Goals

1. Split `app/prompts.py` into a package `app/prompts/` with:
   - `common.py` — language-agnostic blocks.
   - `en.py` — English-specific blocks.
   - `__init__.py` — `get_prompt(language, level)` dispatcher + re-exports.
2. Update three LLM providers (`deepseek.py`, `openai.py`, `fallback.py`) to call `get_prompt(language, level)` instead of importing the static `SYSTEM_MESSAGE`.
3. **No behavior change** for the default path: `get_prompt("en-GB", "default")` must return the same composed string as the current `SYSTEM_MESSAGE` (or as close to it as possible — assembly order and separator preserved).
4. Add focused unit tests for the dispatcher: locale normalisation, fallback to `en`, level block presence.

## Non-goals (deliberately deferred)

- Adding `ru.py`, `de.py`, etc. — separate task per language.
- `language=auto` detection — separate task.
- `toneTags` / `goal` wiring — separate task.
- Renaming or restructuring blocks inside `common`/`en` — keep them as-is for now to make the diff reviewable.
- Changing `GRAMMAR_SCHEMA` — moves to `common.py` unchanged.

## File layout

```
app/prompts/
├── __init__.py        # get_prompt(language, level), re-exports GRAMMAR_SCHEMA
├── common.py          # SYSTEM_INTRO, MODE_BLOCK, OUTPUT_FORMAT_BLOCK,
│                      # REPLACEMENTS_BLOCK, CRITICAL_RULES_BLOCK,
│                      # EXAMPLE_JSON_BLOCK, LATEX_BLOCK, GRAMMAR_SCHEMA
└── en.py              # SVA_BLOCK, ARTICLES_*, CONFUSABLE_*
```

The old `app/prompts.py` is deleted (the package replaces it). Imports `from app.prompts import ...` continue to work because `__init__.py` re-exports `get_prompt` and `GRAMMAR_SCHEMA`.

## Dispatcher contract

```python
def get_prompt(language: str, level: str) -> str:
    """Compose the system message for the given LT language code and level.

    Steps:
    1. Normalise `language` to a 2-letter root: "en-GB" → "en", "ru-RU" → "ru".
       Empty/None → "en".
    2. If a module for the language exists (`prompts.en`, `prompts.ru`, ...),
       use its blocks.
    3. Otherwise: log a warning and fall back to `en`.
    4. Assemble: SYSTEM_INTRO + MODE_BLOCK + <language blocks>
                 + OUTPUT_FORMAT_BLOCK + REPLACEMENTS_BLOCK
                 + CRITICAL_RULES_BLOCK + EXAMPLE_JSON_BLOCK + LATEX_BLOCK.
    """
```

`level` is **not** used to pick blocks — the `MODE_BLOCK` describes both `default` and `picky` semantics and the active value is sent via the user message (`Mode: picky`). The parameter is accepted for future use (e.g. a language module might want a picky-only addition).

**Future fallback option (not implemented now):** instead of falling back to `en`, return a "minimal" prompt = common blocks only, no language-specific section. This makes the model conservative for unknown languages instead of forcing English-tuned article rules onto e.g. Russian. We chose `en` fallback for v1 because it preserves current behaviour; the minimal-fallback is a one-liner to switch on later.

## Locale normalisation rules

- `"en-GB"` → `"en"`, `"en-US"` → `"en"`, `"en"` → `"en"`.
- `"ru-RU"` → `"ru"`, `"ru"` → `"ru"`.
- Case-insensitive: `"EN-gb"` → `"en"`.
- Empty string or `None` → `"en"`.
- Unknown codes (`"klingon"`) → `"en"` after fallback warning.

Implemented as `language.split("-")[0].lower()` for simplicity; the BCP-47 spec allows scripts and regions, but we don't need anything beyond the primary subtag for prompt selection.

## Test plan (unit)

`tests/unit/test_prompts.py`:

- `test_get_prompt_default_language_returns_english_blocks` — `get_prompt("en", "default")` contains SVA and articles blocks.
- `test_get_prompt_normalises_locale` — `get_prompt("en-GB", ...)` == `get_prompt("en", ...)`.
- `test_get_prompt_falls_back_to_en_for_unknown` — `get_prompt("klingon", ...)` returns same content as `en`, with a warning logged.
- `test_get_prompt_contains_mode_block_regardless_of_level` — `MODE_BLOCK` text present in both `default` and `picky` calls (it describes both).
- `test_get_prompt_output_assembly_order` — `SYSTEM_INTRO` appears before `OUTPUT_FORMAT_BLOCK` appears before `LATEX_BLOCK` (catches accidental reorders during future edits).
- `test_grammar_schema_reexport` — `from app.prompts import GRAMMAR_SCHEMA` still works.

Integration smoke: existing 21 tests under `tests/` must pass unchanged.

## Implementation plan (commits)

1. **Add `app/prompts/` package alongside the existing file**, with `common.py` + `en.py` + `__init__.py` that re-exports `SYSTEM_MESSAGE` and `GRAMMAR_SCHEMA` for backward compatibility. This won't conflict — Python prefers the package over a module with the same name only if the file is removed. So step 1 is "create the package next to `prompts.py`, but only as preparation".

   Actually Python does **not** allow `app/prompts.py` and `app/prompts/__init__.py` to coexist — whichever is found first wins. Treat this as one atomic commit:

2. **Replace file with package** in one commit: delete `app/prompts.py`, add `app/prompts/{__init__.py,common.py,en.py}` with `get_prompt` + re-exports `SYSTEM_MESSAGE` (composed via `get_prompt("en", "default")`) and `GRAMMAR_SCHEMA`. Existing imports `from app.prompts import SYSTEM_MESSAGE` keep working as a deprecation bridge.

3. **Switch providers** to use `get_prompt`: update `deepseek.py`, `openai.py`, `fallback.py` to `from app.prompts import get_prompt` and call `get_prompt(language, level)`. Remove the `SYSTEM_MESSAGE` re-export from `__init__.py` (no longer needed). Existing behaviour: providers were passing the same global `SYSTEM_MESSAGE` for every request; now they pass a language-specific one — but since only `en` exists today, output is unchanged for any `language` value (all fall back to `en`).

4. **Add unit tests** for the dispatcher (`tests/unit/test_prompts.py`).

5. **Update `docs/prompt_rules.md`** "Future / Planned" section: cross-link to this doc and mark per-language modules' scaffolding as **done**, distinct from the still-pending per-language content (`ru.py`, `de.py`, etc.).

Each commit individually builds and passes all tests.

## Status

- [ ] Commit 1 — package replaces file (`common.py` + `en.py` + dispatcher; `SYSTEM_MESSAGE` re-exported as bridge)
- [ ] Commit 2 — providers switched to `get_prompt`
- [ ] Commit 3 — unit tests for dispatcher
- [ ] Commit 4 — `prompt_rules.md` cross-link

## How it works once shipped

A grammar-check request flows:

```
client → POST /v2/check { language: "en-GB", level: "default", text: "..." }
   ↓
app/api/v2.py parses → language="en-GB", level="default"
   ↓
app/handlers.py → analyze_with_provider(text, language, level)
   ↓
app/llm/providers.py → analyze_with_json_object(text, language, level)
   ↓
app/llm/deepseek.py → system_message = get_prompt(language, level)
                       ↓
                       app/prompts/__init__.py:get_prompt
                          → normalise "en-GB" → "en"
                          → import app.prompts.en
                          → assemble common + en blocks
   ↓
LLM call with the assembled system_message + user message ("Language: en-GB\nMode: default\nText: ...")
```

Adding a new language later:

1. Create `app/prompts/ru.py` exporting the same surface as `en.py` (e.g. `SVA_BLOCK`, `EXTRA_GUARDS`, ...).
2. Register the module in `__init__.py` (one-line entry in the available-languages map or rely on `importlib` dynamic loading — to be chosen during commit 1).
3. Done — `language=ru` requests now compose with Russian-specific blocks.

No changes needed in providers, handlers, API, or tests outside of the new language module's own tests.
