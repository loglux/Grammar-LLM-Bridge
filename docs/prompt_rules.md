# Prompt Rules

## Design: prompt as a semantic firewall

The system prompt is built from blocks in `app/prompts.py` that fall into two roles, deliberately ordered:

1. **Forbid / Guard** — narrow the model's behaviour. SVA guard, "no style/quote rewrites", "skip inside `$…$`", minimal-fragment discipline. These reduce noise.
2. **Allow / Require** — explicitly re-open a few high-value error classes that a strict reading of the forbid block would suppress (e.g. missing determiners before singular countable nouns).

We treat this pattern as a *semantic firewall*: by default the model is restrained, then specific "ports" are opened for the error types we actually want. New rules should be added in the same shape — a new forbid block needs at least an allow companion if it would block a useful class of corrections, and a new allow block should be narrow enough not to re-introduce style/tone noise.

`MODE_BLOCK` (level=default/picky) tunes how strict the rest of the chain is; it doesn't replace the firewall, just adjusts its sensitivity. Per-language modules planned in [`../ROADMAP.md`](../ROADMAP.md#language-support) will follow the same forbid/allow shape.

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
