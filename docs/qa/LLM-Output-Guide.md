## LLM output keys — detailed guide

We defined a simple response format for the model: JSON with an `errors` array. Each item contains:
- `error_text` — the exact substring from the user’s text,
- `replacement` — the suggested fix,
- `message` — a free-form explanation written by the model.

There is **no explicit type field** in the response. The only signal about “what kind of issue is this?” comes from words inside `message` (e.g., “Subject-verb agreement error”, “Word choice issue”). By inspecting many replies we built a dictionary of these keywords, grouped them into grammar vs. style, and decided which to auto-apply and which to review. This page documents that mapping.

How to read entries:
- **Name** — keyword(s) we see in `message`.
- **Meaning** — what the model is trying to fix.
- **How we treat it** — apply vs. manual review; why.
- **Examples** — typical before/after.

### What the model returns (shape)
- We send text; the model replies with JSON: `{"errors": [ ... ]}`.
- Each error item contains:
  - `error_text` — **verbatim substring** from the input (must match exactly).
  - `replacement` — text to insert instead of `error_text`.
  - `message` — free-form description that embeds the keyword(s) below.
  - Optional flags DeepSeek sometimes sends: `offset`, `length`, `type` (we rely mainly on `error_text`, `replacement`, `message`).
- If the text is perfect, `errors` is an empty array.
- Offsets in the response can be unreliable; we recompute positions ourselves, so exact `error_text` is critical.
- Minimal example (grammar):  
  ```json
  {
    "errors": [
      {
        "error_text": "supplier were",
        "replacement": "supplier was",
        "message": "Subject-verb agreement error: use singular verb."
      }
    ]
  }
  ```
- Example with style noise (word choice) we review:  
  ```json
  {
    "errors": [
      {
        "error_text": "features",
        "replacement": "has",
        "message": "Word choice issue: consider \"has\" for clarity."
      }
    ]
  }
  ```

### Grammar / orthography (apply by default)
- **Spelling error**  
  Meaning: typos, missing letters, swapped letters.  
  How we treat it: apply.  
  Examples: `particularily → particularly`, `Offce → Office`, `immediatly → immediately`.

- **Subject-verb agreement** / **agreement**  
  Meaning: verb form does not match subject number.  
  How we treat it: apply.  
  Examples: `equipment are → is`, `the supplier were → was`, `timeline have been given → has been given`.

- **Incorrect verb form / incorrect phrase / participle**  
  Meaning: wrong verb form or unidiomatic phrase.  
  How we treat it: apply.  
  Examples: `should of been → should have been`, `was write wrong → was written`, `was approximate to → was approximated as`.

- **Tense** (only when a real error)  
  Meaning: tense/participle mismatch with subject or time marker.  
  How we treat it: apply if it fixes an error; flag for review if it merely shifts narrative tense.  
  Examples: `no timeline have been given → has been given` (apply); `ends → ended` in a descriptive passage (review).

- **Comma splice**  
  Meaning: two independent clauses joined by a comma.  
  How we treat it: apply.  
  Examples: `March, others → March; others`, `..., however ...` → split with semicolon.

- **Missing article / missing article before …**  
  Meaning: needs `a/an/the`.  
  How we treat it: apply unless an article already exists immediately before.  
  Examples: `second “i” → the second “i”`, `right-hand side → the right-hand side`, `given value → the given value`.

- **Preposition**  
  Meaning: wrong or extra preposition.  
  How we treat it: apply.  
  Examples: `discuss about → discuss`, `different than → different from`.

- **Plural**  
  Meaning: wrong singular/plural.  
  How we treat it: apply.  
  Examples: `informations → information`, `equipments → equipment`.

- **Apostrophe**  
  Meaning: possessives/omissions.  
  How we treat it: apply.  
  Examples: `teams desk → team’s desk`, `students desk → students’ desk`, `dont → don’t`.

- **Common error: should of …**  
  Meaning: standard `should have` correction.  
  How we treat it: apply.  
  Example: `should of been → should have been`.

### Style / wording / tone (subjective; review)
- **Word choice**  
  Meaning: suggests a different word or phrasing for style/tone.  
  How we treat it: keep but review; can be subjective.  
  Examples: `features → has`, `running slightly behind schedule → experiencing minor delays`.

- **More precise / more natural / informal**  
  Meaning: adjusts formality or naturalness.  
  How we treat it: review; good for fluency, not a hard error.  
  Examples: swap a verb for a more formal one; smooth a colloquial phrase.

- **Tense usage / consistency / inconsistent tense**  
  Meaning: shifts tense without a clear error.  
  How we treat it: review; often stylistic.  
  Examples: `ends → ended`, `features → featured`.

- **Style / Wordiness / Awkward**  
  Meaning: flow and conciseness suggestions.  
  How we treat it: review; do not auto-apply.  
  Examples: remove filler, rewrite to avoid awkward rhythm.

- **Quotation / Punctuation style / Punctuation style for quotes**  
  Meaning: quote marks or spacing style.  
  How we treat it: review; style-dependent.  
  Examples: switching double/single quotes or moving punctuation inside quotes.

- **Missing word after …**  
  Meaning: guidance to add a word for clarity.  
  How we treat it: review; may be stylistic.  
  Example: adding a preposition the model thinks is implied.

- **Hyphenation / Hyphen**  
  Meaning: compound adjective advice.  
  How we treat it: currently filtered out (too noisy).  
  Examples: `open question → open-question`, `soundproof appears → soundproof-appears`.

### Mixed or ambiguous signals
- If a message contains both a grammar keyword and a style keyword, treat it as **review** unless the grammar part is clear (e.g., spelling plus “style” → still apply spelling).
- Very short replacements (articles, commas) can be real fixes; do not reject them solely for length. Use context.

### What we filter in “grammar-only” mode
- Filter out suggestions whose `message` contains: `style`, `wordiness`, `awkward`, `quotation`, `hyphenation`, `hyphen`. Rationale: they are subjective or noisy without a style preset.
- Keep: grammar/orthography items above. Keep `word choice` and `tense usage` so we do not lose common real fixes, but handle them with caution.
- Safeguards already in place:
  - Skip no-ops (`replacement == error_text`).
  - Mask `$...$` and `$$...$$` math and ignore matches inside masks to avoid broken offsets and currency math.
  - Skip adding an article if one is already immediately before the fragment.

### Quick reference table
- Apply: spelling, agreement, incorrect verb form/phrase, clear tense error, comma splice, missing article, preposition, plural, apostrophe, “should of”.
- Review: word choice, more precise/natural/informal, tense usage/consistency (when stylistic), style/wordiness/awkward, quotation style, missing word after.
- Filter out by keyword: style, wordiness, awkward, quotation, hyphenation, hyphen.

Use this guide when triaging model output and when updating filters or prompts.
