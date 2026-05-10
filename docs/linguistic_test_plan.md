# Linguistic Test Plan (Draft)

## Goals
- Structured, repeatable suite to validate grammar/orthography behavior after prompt/model changes.
- Check both: (a) response presence (non-empty content) and (b) correctness of matches per case.

## Categories (initial)
- Articles/determiners: singular countable nouns (plain, with adjectives), fixed expressions to skip, generic plurals.
- Subject–verb agreement: singular/plural subjects, embedded nouns, relative clauses, long-distance agreement.
- Punctuation: missing/extra commas, double punctuation, sentence continuation after $$...$$, inline math punctuation.
- Spelling: common typos, mixed scripts, near-homographs.
- Math/LaTeX handling: inline vs block, punctuation after formulas, capitalization after formulas.
- Collocations/word choice: simple substitutions; avoid style-only changes.
- Misc guards: quote-style changes should not appear; style rewrites should be absent.

## Test Case Specification
For each case store:
- Input text; declared language.
- Expected behavior: must-flag or must-not-flag.
- If must-flag: expected `error_text` and acceptable replacements set.
- Capture whether a response arrived (non-empty content) and whether matches meet expectations.

## Regression Set
- Maintain a small “must pass” subset covering: articles, SVA, LaTeX boundaries, punctuation after formulas, quote-style guard.
- Run on every prompt/model change.

## Next Steps
- Populate concrete cases per category above (cover both positive and negative expectations).
- Implement runner to assert presence/absence and validate `error_text`/replacements against expectations.
- Keep this plan updated when new allow/forbid rules are added to the prompt.

## Seed Test Cases (draft)
- **Articles/determiners**
  - MUST flag: “Yesterday I saw cat sitting on roof.” → error_text: cat/roof; replacements include a/the cat, a/the roof.
  - MUST flag: “She bought new phone yesterday.” → error_text: new phone; replacements include a/the.
  - MUST NOT flag: “Go to school after lunch.” (fixed expression).
- **SVA**
  - MUST flag: “The items in the list is long.” → error_text: is → replacements [are].
  - MUST NOT flag: “The list of items is long.” (correct).
- **Punctuation**
  - MUST flag: “Inside the flat it was very hot” (missing comma after introductory phrase) → error_text: “flat it”.
  - MUST NOT flag: “Inside the flat, it was very hot.”
- **Spelling**
  - MUST flag: “He recieveed the letter.” → error_text: recieveed → replacements [received].
  - MUST NOT flag: “He received the letter.”
- **Math/LaTeX**
  - MUST flag text outside math: “The result $$x=2$$ is correct” (no capitalization change after formula).
  - MUST NOT flag inside math: “The result $$x=2$$.” (no edits inside $$...$$).
- **Collocations/word choice**
  - MUST flag: “He did a decision.” → error_text: did → replacements [made].
  - MUST NOT flag: “He made a decision.”

For each case: store expected match count, `error_text`, and acceptable replacements. Mark “must-not-flag” to assert absence of matches.
