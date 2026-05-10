# Level Modes (default / picky)

Two strictness levels, mirroring LanguageTool's `level` parameter. They tune the sensitivity of the [semantic firewall](./prompt_rules.md) — not what the firewall lets through, but how aggressively the model reports borderline cases.

## API

- **Parameter**: `level` (case-insensitive), accepted in JSON body, form-data, or query string.
- **Values**: `default` (the default) or `picky`. `standard` is treated as `default` for LT compatibility.
- **Missing / unknown** → treated as `default`.

The selected mode is injected into the system prompt via `MODE_BLOCK` (`app/prompts.py`) and forwarded as `Mode: <level>` in the user message.

## Behaviour summary

- **`default`**
  - A single isolated sentence may be interpreted as a note/heading/fragment.
  - Report only clear, high-confidence grammar issues.
  - Skip ambiguous confusable-word cases.
- **`picky`**
  - Treat every input — even one sentence — as standard written prose.
  - Report high- and medium-confidence issues.
  - Apply article and confusable-word rules more aggressively.

## Behaviour by category

| Category | `default` | `picky` |
|---|---|---|
| Articles / determiners | Normal checks; single short sentence may be softer. | Always treat as prose; flag missing determiners even in single sentences. |
| Article — imperatives | Hybrid: do not flag bare singular physical objects ("open window"); flag plural/modified. | Hybrid or strict; if strict, flag everything. |
| Subject–verb agreement | Standard SVA guard (see `prompt_rules.md`). | Same. |
| Punctuation | Optional leniency on missing commas in short single sentences. | Stricter intro-comma and double-punctuation rules (if enabled). |
| Collocations / word choice | Grammar-only collocations; no style rewrites. | Allow broader collocation corrections; still no style rewrites. |
| Spelling | Normal checks. | Same. |
| Math / LaTeX | Skip inside math; punctuation after formulas treated as sentence structure. | Same. |
| Style / quotes guard | No style rewrites; no quote-style changes. | Same. |
| Span discipline | Minimal fragments; no overlaps. | Same. |

## Article policy details

### Determiners — when to flag

| Case | Example | `default` | `picky` |
|---|---|---|---|
| Narrative (clear prose) | She bought new phone yesterday. | ✅ | ✅ |
| Two-sentence input | I found phone on road. / She bought… | ✅ | ✅ |
| Short single narrative | I found phone on road. | ⚠️ | ✅ |
| Adjective + noun | new phone | ✅ | ✅ |
| Nested NP | meeting in office | ✅ | ✅ |
| Proper noun | I visited London. | ❌ | ❌ |
| Uncountable | I need information. | ❌ | ❌ |
| Idiom / fixed expr | go to school / by car | ❌ | ❌ |

⚠️ = `default` may skip; `picky` should flag.

### Imperatives (hybrid policy by default)

| Case | Example | `default` | `picky` |
|---|---|---|---|
| Bare singular physical | Open window. | ❌ | ❌ / ⚠️ |
| Bare singular + context | Open window before lunch. | ❌ | ❌ / ⚠️ |
| Plural | Open windows. | ✅ | ✅ |
| Modified noun | Open new window. | ✅ | ✅ |
| Abstract object | Open file. | ⚠️ | ✅ |

### Single vs multi sentence

| Input | `default` | `picky` | Why |
|---|---|---|---|
| 1 short sentence | ⚠️ | ✅ | May be a note. |
| 2+ sentences | ✅ | ✅ | Treat as prose. |
| Explicit log/note form | ❌ | ❌ | Not prose. |

### Article replacements — allowed shapes

| Replacement | `default` | `picky` | Notes |
|---|---|---|---|
| `a` / `an` / `the` | ✅ | ✅ | Neutral. |
| Possessives (`my` / `your` / …) | ❌ | ❌ | Changes meaning. |
| Demonstratives (`this` / `that`) | ❌ | ❌ | Only when explicit in source. |
| `another` | ❌ | ❌ | New assumption. |

## Engine processing

1. Read `level` from the request (`default` or `picky`).
2. Classify each sentence: single vs paragraph; imperative vs narrative.
3. Apply the tables above per mode.
4. If a cell is ⚠️: `default` may skip, `picky` must flag.

## Regression cases (per mode)

A focused set used to confirm changes don't regress mode behaviour. See [`linguistic_test_plan.md`](./linguistic_test_plan.md) for the broader test plan.

- **Articles**: `cat`/`roof`, `new phone`, `meeting`/`office`; uncountable `information`; idioms `go to school` / `by car`.
- **Imperatives**: `open window`; `open windows`; `open new window`; `open file` (abstract).
- **SVA**: `items in list is long` (flag); `list of items is long` (no flag).
- **Punctuation**: intro-comma cases (only enforced in `picky` if we keep that policy).
- **Spelling**: `recieveed` vs `received`.
- **Math/LaTeX**: no edits inside `$$…$$`; no capitalisation change just after a formula.
- **Collocations**: `did a decision` (flag → `made`) / `made a decision` (no flag).

Observed live (dev profile):

- `tree dogs and three cats` — both modes: no flag (quantifier rule suppresses noise).
- `i saw tree dogs and three cats` — both modes: flag only `tree`→`three`.

## Open / future considerations

These were debated when the modes were first wired and remain TODOs if behaviour drifts:

- Single-sentence leniency in `default`: keep, tighten, or expose as an extra option?
- Imperatives policy: hybrid globally, or strict-in-picky?
- Quantifiers (`some` / `many` / `few` / `little` / `much`): never suggest unless misused.
- Coordinated noun phrases: apply determiner rules consistently across all items.
- Countability: when a noun is dual, suppress missing-article flags unless context disambiguates.
- Genre detection (email / chat / academic) as an explicit parameter, not heuristic.

For the design history that produced the table above — including the decisions that were made, alternatives rejected, and the original prompt sketch — see [`research/level_modes_plan.md`](./research/level_modes_plan.md).

## See also

- [`prompt_rules.md`](./prompt_rules.md) — the forbid/allow firewall the modes plug into, plus the planned per-language module layout (which says `MODE_BLOCK` lives in `common.py`, so level modes compose orthogonally with language).
- [`style_prompt_blocks.md`](./style_prompt_blocks.md) — style/toneTags presets (orthogonal to mode).
- [`research/sva_prompt_block_ab.md`](./research/sva_prompt_block_ab.md) — A/B result for the SVA guard block.
