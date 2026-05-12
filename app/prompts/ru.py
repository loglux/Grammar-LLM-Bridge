"""
Russian-specific prompt blocks: agreement, cases, -тся/-ться, confusables.

Style: English meta-instructions, Russian examples — mirroring the layout
of `en.py`. The dispatcher inserts `BLOCKS` after `MODE_BLOCK` and before
the language-agnostic output / format blocks from `common`.

Deliberately omitted (would generate false positives in Russian):
- article rules (Russian has no articles);
- word-order suggestions (Russian word order is flexible);
- ё/е "missing dot" suggestions (stylistic, not grammatical);
- comma placement heuristics in complex sentences (too rule-heavy
  for a single prompt block — revisit later if needed).
"""

AGREEMENT_BLOCK = """AGREEMENT (СОГЛАСОВАНИЕ) — REPORT REAL MISMATCHES:
- Verb must agree with the subject in number (and in past tense in gender).
- Adjective must agree with its noun in gender, number, and case.
- Examples (flag):
  - "Дети играл во дворе." → "играли" (subject plural).
  - "Новые компьютер стоит на столе." → "Новый компьютер" (adj must be masc. sg.).
  - "Красивая стол." → "Красивый стол" (gender mismatch).
  - "Мы видела фильм." → "Мы видели" (number/person mismatch).
- Examples (do NOT flag — common false positives):
  - "Учитель и ученик пришли." (two singular subjects → plural verb is correct).
  - "Часть студентов написала / написали работу." (collective subject; both forms acceptable).
  - "Молодёжь не любит шум." (singular collective noun is correct as singular)."""

CASES_BLOCK = """CASES (ПАДЕЖИ) — REPORT WRONG CASE AFTER PREPOSITIONS AND VERBS:
- After a preposition, the noun must take the case that preposition requires.
- After a verb, the object must take the case the verb governs.
- Examples (flag):
  - "Иду в магазина." → "Иду в магазин." (preposition "в" with motion → accusative).
  - "Помог мою сестре." → "моей сестре" (verb "помочь" + dative).
  - "Жду ты у входа." → "Жду тебя" (verb "ждать" + accusative/genitive).
  - "На столе лежит книгу." → "лежит книга" (locative state → nominative subject).
- Examples (do NOT flag):
  - "Я живу в Москве." (prepositional case after "в" for location — correct).
  - "Книгу я прочитал вчера." (object fronted for emphasis — word order is flexible, not a case error)."""

TSYA_TSIA_BLOCK = """REFLEXIVE VERBS — -ТСЯ vs -ТЬСЯ:
- Use -ться if the verb is the infinitive ("что делать?"): купаться, научиться, договориться.
- Use -тся if the verb is third-person ("что делает/делают?"): купается, учится, договорятся.
- Examples (flag):
  - "Он любит купатся в реке." → "купаться" (infinitive after "любит").
  - "Она хочет научится плавать." → "научиться".
  - "Они не могут договорится о цене." → "договориться".
  - "Ребёнок учиться писать." → "учится" (3rd person, no soft sign).
- Test by asking "что делать?" (→ -ться) vs "что делает?" (→ -тся)."""

CONFUSABLES_BLOCK = """RUSSIAN CONFUSABLES — SLITNO / RAZDELNO PAIRS:
Flag only clear-cut cases; when meaning is ambiguous between the two forms,
leave it alone.
- также (adverb, "also/in addition") vs так же (modifier + particle, "in the same way as"):
  - "Я также хочу пойти." (also = together) — correct.
  - "Он поступил так же, как и я." (in the same manner as I = separate) — correct.
- тоже (adverb, "too/also") vs то же (pronoun + particle, "the same thing"):
  - "Я тоже пойду." (also = together) — correct.
  - "Он сказал то же самое." (the same thing = separate) — correct.
- чтобы (conjunction, "in order to / so that") vs что бы (pronoun + particle):
  - "Я пришёл, чтобы помочь." (purpose = together) — correct.
  - "Что бы ни случилось, я приду." (whatever happens = separate) — correct.
- одеть (to dress someone/something) vs надеть (to put on oneself):
  - "Надень куртку." (put on yourself) — correct.
  - "Одень ребёнка." (dress someone else) — correct."""

# Ordered list of blocks contributed by this language module.
# The dispatcher inserts these after MODE_BLOCK and before the
# language-agnostic output / format blocks from `common`.
BLOCKS = [
    AGREEMENT_BLOCK,
    CASES_BLOCK,
    TSYA_TSIA_BLOCK,
    CONFUSABLES_BLOCK,
]
