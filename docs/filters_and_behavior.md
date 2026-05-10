# Filters & Behavior 

## Runtime settings (current container)
- Model: DeepSeek (openai-compatible), `LLM_MODEL=deepseek-chat`
- GRAMMAR_ONLY: false (style/word choice not filtered)
- Prompt additions: General English context; ignore curly vs straight quotes/apostrophes.

## Active filters in code
- GRAMMAR_ONLY (when true): drop messages containing style keys (`style`, `wordiness`, `awkward`, `quotation`, `hyphenation`, `hyphen`), except if message contains `punctuation`/`comma`.
- No-op replacement: skip if `replacement == error_text`.
- Mask LaTeX: skip matches inside `$...$` / `$$...$$` ranges.
- Redundant article: skip if replacement just adds `the/a/an` and article already exists immediately before.
- Capital-letter off-boundary: drop “capital letter/sentence start” if offset not after start or `.?!`.
- Typography gating: env `TYPOGRAPHY_CHECK` (default true). If `GRAMMAR_ONLY=true` we drop style+typography; if `GRAMMAR_ONLY=false` and `TYPOGRAPHY_CHECK=false` we drop only typography keys (`ellipsis`, `quotation`, `quote`, `apostrophe`, `dash`, `hyphen`, `hyphenation`, `usage`). Typographic keys match whole words to avoid false hits (e.g., `dash` in `dashboards`).
- Leading punctuation guard: drop if replacement starts with punctuation already present immediately before error_text.
- Trailing punctuation guard: drop if replacement ends with punctuation already present immediately after error_text (covers `, . ; : ! ?`).
- Single-token expansion guard: drop if `error_text` is one token and replacement starts with the same token plus extra tokens (e.g., `hangs -> hangs loose`).
- Overlap handling: we track `used_ranges` (start, end) to avoid overlapping matches; non-overlapping spans are allowed even if starts coincide.
- Deduplication: after mapping to original text, if multiple matches hit the same `(offset, length)`, keep the first; merge only new replacement values into it, drop pure duplicates.

## Known model quirks (DeepSeek)
- May return minimal fragments (one word) for larger issues; offsets remain correct.
- Sometimes repeats existing punctuation/commas (handled by trailing guard).
- Styling noise when GRAMMAR_ONLY=false (word choice, rephrasings).
- Sample6 observation: after fixing `period..`, model suggested `And starts` (capitalising `and` as new sentence). Treat as potential style/overreach; currently not filtered.

## Not implemented (ideas)
- Duplicate-on-same-span deduplication.
- Proper handling of replacements arrays from model (we currently expect `replacements` list but often use the first item).
- Goal/toneTags-based style control.
