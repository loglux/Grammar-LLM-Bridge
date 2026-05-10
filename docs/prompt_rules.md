# Prompt Rules (DeepSeek json_object) – Internal

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
