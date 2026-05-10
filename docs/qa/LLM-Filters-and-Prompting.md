## LLM Filters & Prompting

> **Snapshot as of December 2025.** This document captures the response patterns we observed when validating the original DeepSeek (`deepseek-chat`) integration, plus the post-processing filters that codify those observations. The filters themselves still live in [`../filters_and_behavior.md`](../filters_and_behavior.md); newer model behaviours (DeepSeek v4 family, GPT-5 family) may differ. Use as background, not as current spec.

### Backend / mode (at the time of writing)
- Model: `deepseek-chat` via `https://api.deepseek.com`, `GRAMMAR_ONLY=true`.
- Prompt: JSON schema (`json_object`), minimal fragments, no overlaps, array only.

### Response patterns observed
- Keys that are **grammar**: subject-verb agreement, tense consistency (sometimes overzealous), comma splice, missing articles, spelling.
- Keys that are **style/word choice**: “word choice issue”, “tense usage”, “running slightly behind schedule…”, hyphen advice (“Missing hyphen…”, “Inconsistent hyphen usage…”), punctuation style for quotes.
- DeepSeek sometimes labels style-like issues without the word “style”, so message keywords matter.

### Current filters
- Drop messages whose `message` contains: `style`, `wordiness`, `awkward`, `quotation`, `hyphenation`, `hyphen`.
- Skip no-op (`replacement == error_text`).
- Mask `$...$` / `$$...$$`, skip matches inside those ranges.
- Skip redundant article insertion if an article already precedes the fragment (`the/a/an`).

### What still passes (by design)
- Grammar, spelling, agreement, comma splices.
- Word choice / tense suggestions (e.g. “features → has”, “ends → ended”) — treated as potential noise, not filtered yet.
- Hyphen-like advice that does not include the above keywords.

### Why this matters for future style rules
- DeepSeek emits mixed labels (grammar + style) in one stream; filtering relies on message keywords.
- If we add explicit style goals later, we can allow “word choice/tense/hyphen” selectively instead of blanket filtering.
- Current setup prioritises correctness and suppresses obvious stylistic noise; borderline style changes are noted in QA.

### Build/run
- Build in `grammar/`: `docker build -t grammar-llm-bridge:latest .`
- Run: `docker run -d --name Grammar-LLM-Bridge -p 9019:8000 -e OPENAI_API_KEY=... -e OPENAI_BASE_URL=https://api.deepseek.com -e LLM_MODEL=deepseek-chat -e GRAMMAR_ONLY=true grammar-llm-bridge:latest`
