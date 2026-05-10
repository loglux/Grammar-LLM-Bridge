# Standard vs Picky – Rule Differences (Draft)

## Table of differences by category

| Category            | Standard (default)                                      | Picky                                               |
|---------------------|---------------------------------------------------------|-----------------------------------------------------|
| Articles/determiners| May allow leniency for a single short sentence (optional); otherwise normal checks. Decide if single-sentence shorthand can be softer. | Always treat as prose; flag missing determiners even in single sentences. |
| Articles – Imperatives| **Choose policy:** Hybrid recommended (do not flag bare singular objects like “open window”; flag plural/modified). | Hybrid or Strict; if Strict, flag “open window”, always flag plural/modified. |
| SVA                 | Normal SVA checks; no change.                           | Same (strict); ensure no over-flagging due to SVA guard. |
| Punctuation         | Optional leniency on missing commas in short single sentences; idioms may be softer. | Stricter punctuation (intro commas, double punctuation), if desired. |
| Collocations/word choice| Basic grammar-only collocations; avoid style-y rewrites. | Allow more collocation/word-choice corrections if they are clearly grammatical (still no style rewrites). |
| Spelling            | Normal spelling checks.                                 | Same.                                               |
| Math/LaTeX          | Skip inside math; punctuation/caps after formulas treated as sentence structure. | Same.                                               |
| Style/quotes guard  | No style rewrites; ignore quote-style changes.          | Same.                                               |
| Span discipline     | Minimal fragments; no overlaps.                         | Same.                                               |

## Decisions to make
- Should standard be softer on single-sentence shorthands (articles/punctuation/collocations)? Define precise cases.
- Imperatives policy: Hybrid vs Strict; tie to level or pick one globally.
- Punctuation strictness: do we want stricter intro-comma rules in picky?
- Collocations: allow broader corrections in picky or keep parity?

## Suggested prompt handling
- Option A: One prompt with MODE instructions + level passed in; rely on model to adjust behavior.
- Option B: Two prompts (standard/picky) with explicit differences per the table above; select in code by `level`.

## Regression matrix impact
- Mark each test case with expected behavior for standard vs picky based on the table. Update test runner accordingly.

## Detailed policy table (for prompt/tests)

### Articles / Determiners
| Case                           | Example                                | standard | picky | Notes                                |
| ------------------------------ | -------------------------------------- | -------- | ----- | ------------------------------------- |
| Narrative (clear prose)        | She bought new phone yesterday.        | ✅        | ✅     |                                       |
| Two sentences                  | I found phone on road. / She bought…   | ✅        | ✅     | Paragraph ⇒ prose                     |
| Short single narrative         | I found phone on road.                 | ⚠️       | ✅     | Standard may allow note/shorthand     |
| Adj + noun                     | new phone                              | ✅        | ✅     | Strong trigger                        |
| Nested NP                      | meeting in office                      | ✅        | ✅     | Both need articles                    |
| Proper noun                    | I visited London.                      | ❌        | ❌     | Never                                 |
| Uncountable                    | I need information.                    | ❌        | ❌     | Never                                 |
| Idiom                          | go to school / by car                  | ❌        | ❌     | Never                                 |

### Imperatives (HYBRID recommended)
| Case                    | Example                       | standard | picky  | Notes                                |
| ----------------------- | ----------------------------- | -------- | ------ | ------------------------------------- |
| Bare singular physical  | Open window.                  | ❌        | ❌ / ⚠️ | Ellipsis acceptable                   |
| Bare sing. + context    | Open window before lunch.     | ❌        | ❌ / ⚠️ | Still acceptable                      |
| Plural                  | Open windows.                 | ✅        | ✅      | Likely “the windows”                  |
| Modified noun           | Open new window.              | ✅        | ✅      | Article required                      |
| Abstract object         | Open file.                    | ⚠️       | ✅      | Standard may treat as UI command      |

⚠️ = standard can be lenient; picky should flag.

### Single vs Multi sentence
| Input                  | standard | picky | Why               |
| ---------------------- | -------- | ----- | ----------------- |
| 1 short sentence       | ⚠️       | ✅     | May be a note     |
| 2+ sentences           | ✅        | ✅     | Treat as prose    |
| Explicit log/note form | ❌        | ❌     | Not prose         |

### Semantics of replacements (articles)
| Case             | standard | picky | Notes                  |
| ---------------- | -------- | ----- | ---------------------- |
| a / an / the     | ✅        | ✅     | Neutral                |
| my/your/his/etc  | ❌        | ❌     | Changes meaning        |
| this/that        | ❌        | ❌     | If not in text         |
| another          | ❌        | ❌     | New assumption         |

## Engine processing (checklist)
1. Read `level` (standard/picky).
2. Classify sentence(s): single vs paragraph; imperative vs narrative.
3. Apply table rules per mode.
4. If cell = “⚠️”: standard may skip; picky must flag.

## Regression subset (per level)
- Articles: cat/roof, new phone, meeting/office; uncountable/info; idioms.
- Imperatives: open window; open windows; open new window; open file (abstract).
- SVA: items in list is long (flag); list of items is long (no flag).
- Punctuation: intro comma cases (if we decide to enforce).
- Spelling: recieveed vs received.
- Math: no edits inside $$...$$; no cap change just after formula.
- Collocations: did a decision (flag) / made a decision (no flag).

## Additional policy areas to consider (future)

### Critical (likely to surface)
- DETERMINERS – QUANTIFIERS: Do not suggest quantifiers (some/many/few/little/much) unless the text misuses a quantifier.
- PLURAL NOUNS: Do not require articles for generic plural nouns; report article issues only when specificity is explicit.
- PREPOSITIONAL NPs (at/in/on + noun): respect fixed prepositional expressions and regional variants (e.g., BrE “in hospital”).

### Hidden (show up later)
- COUNTABILITY: If a noun can be both countable and uncountable, do not flag missing articles unless context makes countability explicit.
- COORDINATED NOUNS: In coordinated noun phrases, apply determiner rules consistently across all items.
- ELLIPSIS: Allow ellipsis in questions and short conversational prompts unless level=picky.

### Optional (defer)
- Discourse/coreference for repeated nouns (phone → the phone).
- Genre detection (email/chat/academic) as an explicit parameter, not heuristic.
