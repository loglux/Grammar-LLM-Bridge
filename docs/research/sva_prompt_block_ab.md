
> **[Historical — Dec 2025 A/B]** Result of comparing the SVA guard block on/off
> across DeepSeek and OpenAI. Conclusions fed into the current
> `app/prompts.py` (the SVA_BLOCK lives there). Kept for reference.

# Subject–Verb Agreement Prompt Update (Dec 21, 2025)

## What changed
- Added an SVA guard block to all system prompts in `app.py` (json_object / json_schema / fallback).
- The block warns against false positives on “is/are” when the true subject is singular:
  - GOOD: “The list of new items **is** long.” → do not change “is”.
  - GOOD: “A key feature of these models **is** their speed.” → do not change “is”.
  - BAD: “The items in the list **is** long.” → must change to “are”.
  - GOOD: “The horses **runs** fast.” → flag “runs” → “run”.
  - BAD: “The list of approved items … **is** now final.” → do not flag “is”.

## Tests
### Suite: `qa_sva.json` (29 targeted cases, DeepSeek `deepseek-chat`)
- Folder: `qa-results/ad-hoc/sva-ab-20251221-121157/`
- Result: SVA block reduced FN, no new FP:
  - Fixed misses: `series were→was`, `group … are→is`, `each of the proposals are→is`.
  - All “no-change” constructions (list with relative clause, catalogue, news/mathematics/statistics, one/each/another of … is) stayed untouched.

### OpenAI models (partial runs)
- `gpt-4.1-mini` (limit=5, folder `sva-ab-20251221-121810`): model is noisy (3 hits where 1 expected); SVA block did not worsen or improve counts.
- `gpt-4.1` (limit=10, folder `sva-ab-20251221-122030`): same noise pattern; SVA block neutral.

## Conclusions
- DeepSeek: SVA few-shot block is beneficial (reduces FN, no FP on our SVA suite).
- OpenAI (4.1/mini): block is neutral; model still noisy on SVA. Consider server-side post-filters if needed.

## Relevant files
- Prompt changes: `app.py` (system_message blocks for json_object/json_schema/fallback).
- Test suite: `qa-results/quality/qa_sva.json`.
- A/B runs: `qa-results/ad-hoc/sva-ab-*` as noted above.
