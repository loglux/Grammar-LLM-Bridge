level modes (default / picky)
-------------------------------

api
- parameter: `level` (case-insensitive) in json body, form-data, or query string.
- allowed values: `default` (default), `picky`.
- if absent/unknown → treated as `default`.

prompt behaviour
- mode block added to all providers (openai json schema, deepseek json_object, fallback).
- `default`:
  - single sentences may be treated as notes/headings/fragments.
  - report only clear/high-confidence grammar issues.
  - skip ambiguous confusable-word cases.
- `picky`:
  - treat all input as standard prose (even one sentence).
  - report high- and medium-confidence grammar issues.
  - apply article and confusable-word rules more aggressively.

article policy tweak
- do NOT report missing determiners for:
  - proper nouns
  - plural generic nouns
  - nouns already quantified (numbers/quantifiers)
  - mass/uncountable nouns
  - fixed expressions (go to school, at home, in bed, by car, at work)

current observed behaviour (dev, 9019)
- `tree dogs and three cats`
  - `default`: no flags
  - `picky`: no flags (quantifier rule suppresses article noise)
- `i saw tree dogs and three cats`
  - `default`: flags only “tree”→“three”
  - `picky`: flags only “tree”→“three”

notes / follow-ups
- if we want `picky` to always catch a leading-word confusable (e.g., “tree”→“three”), add an explicit confusable trigger for sentence-initial tokens.
- `level` is parsed and passed into prompts; logging of `level` is still minimal (can add request logging if needed).
