"""
English-specific prompt blocks: SVA guard, articles policy, confusable words.

These blocks assume the text under check is in English. They reference
English grammar (subject-verb agreement against the head noun, missing
determiners, confusable-word pairs typical for English) and would produce
false positives on languages that don't share these features.

When adding a new language module, mirror this surface: export a set of
top-level constants that the dispatcher in `app/prompts/__init__.py` will
assemble after `MODE_BLOCK`.
"""

SVA_BLOCK = """SUBJECT–VERB AGREEMENT (AVOID FALSE POSITIVES):
- The subject is not the nearest plural noun. Analyse the whole phrase.
- GOOD: "The list of new items is long." → subject = list (singular), DO NOT change "is".
- GOOD: "A key feature of these models is their speed." → subject = feature (singular), DO NOT change "is".
- BAD: "The items in the list is long." → subject = items (plural), MUST change "is"→"are".
- GOOD: "The horses runs fast." → flag "runs" → ["run"].
- BAD: "The list of approved items, which contains many entries, is now final." → DO NOT flag "is"."""

ARTICLES_TRIGGER = """ARTICLES – TRIGGER (HIGH CONFIDENCE, MUST REPORT):
- In standard prose, a missing determiner before a singular countable common noun MUST be reported.
- Determiners include: a/an, the, this/that/these/those, my/your/his/her/its/our/their, some/any, each/every, no, another,
  numbers (one/2/three...), and possessives (John's).
- If the noun phrase begins with adjectives but has no determiner, still report it (e.g., "new phone" needs "a/the")."""

ARTICLES_DO_NOT_REPORT = """ARTICLES – DO NOT REPORT:
- Do NOT report for proper nouns, plural generic nouns, nouns already quantified (numbers/quantifiers), mass/uncountable nouns, or common fixed expressions (go to school, at home, in bed, by car, at work)."""

ARTICLES_REPLACEMENTS = """ARTICLES – REPLACEMENTS CONSTRAINT:
- Replacements MUST preserve the original meaning of the sentence.
- Do NOT introduce new semantic assumptions.
- Do NOT introduce possessive determiners (my/your/his/her/its/our/their) unless possession is explicitly indicated in the text.
- Prefer neutral articles only:
  - a/an for first mention or nonspecific reference
  - the for clearly specific reference"""

CONFUSABLE_VERB_OBJECT = """CONFUSABLE WORDS – VERB OBJECT HEURISTIC:
- If a noun is the direct object of a verb, consider whether that noun is a plausible object for that verb.
- For highly common verbs with strong object preferences (read, write, wear, eat, drink, pay, win, lose), a confusable correction may be high-confidence."""

CONFUSABLE_CONFIDENCE = """CONFUSABLE WORDS – CONFIDENCE LABELS:
- If the context suggests a confusion but is not definitive, still report it with message starting with "Possible confusion:".
- Keep replacements to the most likely alternative (one option)."""

# Ordered list of blocks contributed by this language module.
# The dispatcher inserts these after MODE_BLOCK and before the
# language-agnostic output / format blocks from `common`.
BLOCKS = [
    SVA_BLOCK,
    ARTICLES_TRIGGER,
    ARTICLES_DO_NOT_REPORT,
    ARTICLES_REPLACEMENTS,
    CONFUSABLE_VERB_OBJECT,
    CONFUSABLE_CONFIDENCE,
]
