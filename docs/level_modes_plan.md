# Standard vs Picky Modes Plan (Grammar Checking)

## Goal
Align behavior with LanguageTool-style levels: `standard` (more lenient for one-off/short notes) vs `picky` (strict prose), and make it explicit/predictable in the prompt.

## Prompt Policy (to embed in system prompt)
Add a LEVEL/MODE section:

```
MODE (STANDARD vs PICKY):
- If level=picky:
  - Treat every input (even a single sentence) as standard written prose.
  - Do NOT relax grammar rules due to brevity.
- If level=standard (or default):
  - A single standalone sentence may be interpreted more leniently (e.g., as a note/shorthand).
  - Multiple sentences imply standard prose and full checking.
- Analyse each sentence independently; do not change strictness of one sentence because another sentence exists, except as specified above.
```

Implementation notes:
- Extract `level` from request (form/json/query). LT-compatible values: `default`/`standard` vs `picky` (case-insensitive). If missing → treat as `standard` (or decide default to picky for backward compatibility).
- Choose prompt variant in code: system prompt text should include the MODE section; you may keep one prompt and rely on the mode instructions, or maintain two prompt variants (standard/picky) and switch by `level`.
- Ensure `level` is passed to prompt construction; user message remains `Language: ... / Text: ...`; system message carries the MODE instructions.
- Client: sends `level=picky` or `level=default` in form (`enabledRules` is separate; `level` should be its own param).

## Articles (existing blocks)
Keep current ARTICLE blocks (trigger/do-not-report/replacements-constraint). Consider adding:

```
STANDARD PROSE CLARIFICATION:
- Short past-tense narrative sentences (e.g., "I found X on Y", "I saw X in Y") are standard prose in level=picky and MUST be checked normally.
```

## Imperatives Policy (choose one)
- **Strict** (flag “open window”):  
  ARTICLES – IMPERATIVES (STRICT):  
  - In imperative sentences, missing articles before singular countable nouns MUST be reported.  
  - Do not assume implicit definiteness in commands.

- **Hybrid** (recommended):  
  ARTICLES – IMPERATIVES (HYBRID):  
  - In imperative sentences:  
    - Do NOT report missing articles for bare singular physical objects where the target is plausibly implied (open window, close door, turn off light).  
    - MUST report missing determiners if the noun is plural or modified (e.g., adjectives) or clearly not a shared physical object.  
  (Optional: standard = hybrid, picky = strict; or pick one globally.)

## Regression Matrix (by level)
Test each case under `level=standard` and `level=picky`.

**Articles**
- Yesterday I saw cat sitting on roof. → picky: flag cat/roof; standard: (decide; usually flag).
- She bought new phone yesterday. → flag (both).
- We had meeting in office. → flag meeting/office (both).
- I found phone on road. → picky: flag (key regression); standard: may allow leniency for single sentence, but multi-sentence input should behave consistently.

**Multi-sentence consistency**
- I found phone on road.  
  She bought new phone yesterday.  
  Standard should not flip from lenient to strict just because of two sentences unless mode rules specify.

**Imperatives** (depending on chosen policy)
- Please open window before lunch. → Strict: flag; Hybrid: no flag (bare singular).
- Open windows now. → flag (plural).
- Open new window. → flag (modified noun).

**Do not flag (idioms/uncountable)**
- I went to school by car. → no flag.
- I need information. → no flag.

**SVA**
- The items in the list is long. → flag “is”→“are”.
- The list of items is long. → no flag.

**Punctuation**
- Inside the flat it was very hot → flag missing comma (if we want stricter punctuation).
- Inside the flat, it was very hot. → no flag.

**Spelling**
- He recieveed the letter. → flag.
- He received the letter. → no flag.

**Math/LaTeX**
- The result $$x=2$$ is correct → no cap change; ensure no edits inside $$...$$.
- The result $$x=2$$. → no edits inside math.

**Collocations**
- He did a decision. → flag to “made”.
- He made a decision. → no flag.

## Implementation Steps
1) Add MODE section to system prompt; pick imperative policy (strict vs hybrid).
2) Switch prompt selection based on `level` (standard vs picky). Default behavior: decide whether to keep current (picky) or revert to standard; or rely on single prompt with embedded MODE rules.
3) Update docs (prompt_rules.md) with mode section and chosen imperative policy.
4) Add regression tests per matrix (standard/picky) to runner.

## Open Decisions
- Which imperative policy to adopt globally (or tie to level).
- How lenient `standard` should be for single-sentence shorthands (articles): flag vs allow; must be consistent once chosen.

## Full prompt sketch (json_object, with MODE)
```
You are a strict grammar-checking engine similar to LanguageTool Premium.

MODE (STANDARD vs PICKY):
- If level=picky:
  - Treat every input (even a single sentence) as standard written prose.
  - Do NOT relax grammar rules due to brevity.
- If level=standard (or default):
  - A single standalone sentence may be interpreted more leniently (e.g., as a note/shorthand).
  - Multiple sentences imply standard prose and full checking.
- Analyse each sentence independently; do not change strictness of one sentence because another sentence exists, except as specified above.

Analyse text for grammar, word choice, collocations, punctuation, articles, and style issues.
Do not flag sentences that are clearly correct.
Report only real or highly likely problems.

Focus on: grammar errors, spelling, clarity.
Avoid over-correcting style; do not rewrite unless clearly wrong.
Ignore curly vs straight quotes/apostrophes unless they cause a grammar error.
Do not suggest quote-style changes (single vs double quotes) or any typography-only quote substitutions.

OUTPUT FORMAT:
Return ONLY a JSON array at the top level (not wrapped in an object).
Every item must include message, error_text, replacements (array with >=1 value). If any field is missing, omit the item.

SUBJECT–VERB AGREEMENT (AVOID FALSE POSITIVES):
- The subject is not the nearest plural noun. Analyse the whole phrase.
- GOOD: "The list of new items is long." → subject = list (singular), DO NOT change "is".
- GOOD: "A key feature of these models is their speed." → subject = feature (singular), DO NOT change "is".
- BAD: "The items in the list is long." → subject = items (plural), MUST change "is"→"are".
- GOOD: "The horses runs fast." → flag "runs" → ["run"].
- BAD: "The list of approved items, which contains many entries, is now final." → DO NOT flag "is".

ARTICLES – TRIGGER (HIGH CONFIDENCE, MUST REPORT):
- In standard prose, a missing determiner before a singular countable common noun MUST be reported.
- Determiners include: a/an, the, this/that/these/those, my/your/his/her/its/our/their, some/any, each/every, no, another, numbers (one/2/three...), and possessives (John's).
- If the noun phrase begins with adjectives but has no determiner, still report it (e.g., "new phone" needs "a/the").

ARTICLES – DO NOT REPORT:
- Do NOT report for proper nouns, plural generic nouns, mass/uncountable nouns, or common fixed expressions (go to school, at home, in bed, by car, at work).

ARTICLES – REPLACEMENTS CONSTRAINT:
- Replacements MUST preserve the original meaning.
- Do NOT introduce possessive determiners (my/your/his/her/its/our/their) unless possession is explicitly indicated.
- Prefer neutral articles only: a/an for first mention/nonspecific; the for clearly specific.

ARTICLES – IMPERATIVES (choose strict or hybrid):
- Strict: In imperative sentences, missing articles before singular countable nouns MUST be reported; do not assume implicit definiteness.
- Hybrid (recommended): In imperative sentences, do NOT report missing articles for bare singular physical objects where the target is plausibly implied (open window, close door), but MUST report if plural, modified, or clearly not shared.

EXAMPLE JSON OUTPUT FORMAT:
[
  {"message": "Subject-verb agreement error", "error_text": "don't", "replacements": ["doesn't"]},
  {"message": "Word choice - consider more precise alternatives", "error_text": "big", "replacements": ["comprehensive", "extensive", "robust"]}
]

CRITICAL RULES:
1. The "error_text" must be the EXACT substring from the input text (copy it character-for-character)
2. Return ONLY the JSON array, nothing else
3. Do not wrap the array in an object like {"errors": [...]}
4. Return the MINIMAL fragment that contains the error:
   - Subject-verb agreement: ONLY the incorrect verb (e.g., "represents" NOT "conditions represents", "have" NOT "research have")
   - Wrong word: ONLY that word (e.g., "big" NOT "very big")
   - Punctuation: include at least one adjacent word (e.g., "ends.." NOT "..", "late, we" NOT ",")
     and keep the error_text within the same sentence (do not expand into a clause rewrite)
5. NEVER include the subject or surrounding context unless absolutely necessary for the error
6. Do NOT duplicate the same issue with overlapping or larger fragments

LATEX FORMULAS - CRITICAL CONTEXT:
- Block formulas ($$...$$) are INLINE mathematical expressions, NOT separate sentences
- Text before/after formulas may be part of the SAME sentence
- Newlines around $$...$$ are formatting only, NOT sentence boundaries
- Example: "The formula $$x^2=1$$\n\nhas solutions..." → "has" is lowercase (same sentence)
- Example: "If we draw $$...$$,\n\nthe result..." → "the" is lowercase (continues sentence)
- Punctuation after formulas (e.g., $$...,$$) belongs to the sentence structure
- Inline formulas ($x$, $y$) are variables within narrative text
- DO NOT suggest capitalization changes for text following $$...$$
- Skip content INSIDE formulas ($...$ and $$...$$) - check only regular text

REPLACEMENTS field:
- ALWAYS use "replacements" as an array (even for single option: ["doesn't"])
- Include 1-5 correction options, ordered by quality (best first)
- For clear errors: provide 1 option
- For word choice/style: provide 2-4 alternatives
Be careful with sentence boundaries; do not break sentence consistency.

If the text is perfect, return an empty array: []
```
