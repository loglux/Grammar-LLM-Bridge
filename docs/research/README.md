# Research notes

Background notes, comparisons, and design discussions accumulated while building Grammar-LLM-Bridge. Read these to understand *why* decisions were made or *what* alternatives were considered — not as authoritative current documentation.

For current architecture and operational docs, see [`../architecture/`](../architecture/) and the project README.

## LanguageTool API

- [API_REQUEST_RESPONSE_EXAMPLES.md](API_REQUEST_RESPONSE_EXAMPLES.md) — captured request / response samples from the wire.
- [LANGUAGETOOL_ADDITIONAL_APIS.md](LANGUAGETOOL_ADDITIONAL_APIS.md) — endpoints beyond `/v2/check`.
- [LANGUAGETOOL_FILTERING_PARAMS.md](LANGUAGETOOL_FILTERING_PARAMS.md) — `enabledOnly`, `disabledRules`, etc.
- [LANGUAGETOOL_GOALS_TONETAGS.md](LANGUAGETOOL_GOALS_TONETAGS.md) — premium goals / toneTags parameters.
- [UNDOCUMENTED_LT_PARAMETERS.md](UNDOCUMENTED_LT_PARAMETERS.md) — parameters seen on the wire but not in swagger.
- [PROVIDER_MODES.md](PROVIDER_MODES.md) — provider-mode landscape.
- [QA_API_STATUS.md](QA_API_STATUS.md) — Bridge ↔ LanguageTool feature gaps.

## Response shape

- [RESPONSE_FORMAT_COMPARISON.md](RESPONSE_FORMAT_COMPARISON.md) — high-level response shape comparison.
- [RESPONSE_STRUCTURE_COMPARISON.md](RESPONSE_STRUCTURE_COMPARISON.md) — detailed structure comparison.

## Languages

- [QA_LANGUAGE_DETECTION.md](QA_LANGUAGE_DETECTION.md) — comparison of fastText / langid / cld3 / langdetect for the eventual `language=auto` implementation.

## Style and tone

- [style_presets.md](style_presets.md) — current style preset descriptions (focus/avoid for each preset).
- [style_configs_plan.md](style_configs_plan.md) — plan for parametric style configs via prompt blocks.
- [GRAMMAR_CHECK_STYLES.md](GRAMMAR_CHECK_STYLES.md) — grammar-check style notes.

## Synonyms / paraphrase (future feature)

- [LLM_SYNONYMS_APPROACH.md](LLM_SYNONYMS_APPROACH.md) — LLM-based synonym generation design.
- [PARAPHRASE_SYNONYMS_API_SCHEMA.md](PARAPHRASE_SYNONYMS_API_SCHEMA.md) — proposed API surface.
- [PARAPHRASE_SYNONYMS_EXAMPLES.md](PARAPHRASE_SYNONYMS_EXAMPLES.md) — concrete examples.
- [SYNONYMS_API_UPDATE.md](SYNONYMS_API_UPDATE.md) — incremental update notes.
- [WORDNET_DIRECT_ACCESS.md](WORDNET_DIRECT_ACCESS.md) — direct WordNet access as an alternative.
- [RUSSIAN_SYNONYMS.md](RUSSIAN_SYNONYMS.md) — Russian synonym sources.

## Multi-LLM and modes

- [MULTI_LLM_DESIGN.md](MULTI_LLM_DESIGN.md) — design for routing across multiple LLM providers.
- [OPENROUTER_FREE_MODELS.md](OPENROUTER_FREE_MODELS.md) — OpenRouter free-tier exploration.

## Auth

- [AUTH_DESIGN_DISCUSSION.md](AUTH_DESIGN_DISCUSSION.md) — early design discussion. The implementation is now documented in [`../auth/`](../auth/) (AUTH_GUIDE / AUTH_CUSTOMIZATION).

## QA

- [QA_MULTIVARIANT_REPLACEMENTS.md](QA_MULTIVARIANT_REPLACEMENTS.md) — multi-variant replacement handling.
- [live_check_strategy.md](live_check_strategy.md) — client-side live-check strategy (debounce, scoping, version-tagging).

## Project history

- [REFACTORING.md](REFACTORING.md) — [historical, 2025-12-28] the monolith-to-modules refactor. Useful for archaeology; the current layout is in [`../architecture/MODULE_STRUCTURE.md`](../architecture/MODULE_STRUCTURE.md).
- [level_modes_plan.md](level_modes_plan.md) — [historical, 2025-12] design discussion that produced the `default`/`picky` mode behaviour. Canonical reference today is [`../LEVEL_MODES.md`](../LEVEL_MODES.md).
- [sva_prompt_block_ab.md](sva_prompt_block_ab.md) — [historical, 2025-12 A/B] result of toggling the SVA guard block across DeepSeek and OpenAI models. The block now lives in `app/prompts.py`.
