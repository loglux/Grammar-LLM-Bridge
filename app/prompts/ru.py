"""
Russian-specific prompt blocks: agreement, cases, -тся/-ться, confusables.

Style: English meta-instructions, Russian examples — mirroring the layout
of `en.py`. The dispatcher inserts `BLOCKS` after `MODE_BLOCK` and before
the language-agnostic output / format blocks from `common`.

Deliberately omitted (would generate false positives in Russian):
- article rules (Russian has no articles);
- word-order suggestions (Russian word order is flexible);
- ё/е "missing dot" suggestions (stylistic, not grammatical);
- comma rules outside the five explicit classes in COMMAS_BLOCK
  (e.g. before "и" in compound sentences, optional comparatives with
  "как", homogeneous members — the model handles these natively and
  explicit guidance tends to over-flag).
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

COMMAS_BLOCK = """COMMAS (ЗАПЯТЫЕ) — REPORT CLEAR MISSING COMMAS, NOT STYLE:

Five clear-cut classes. Outside these, do NOT suggest commas.

1) Subordinate clauses: a comma at the boundary with что, чтобы, если,
   когда, потому что, так как, хотя, etc.
   - "Я знаю что он придёт." → "Я знаю, что он придёт."
   - "Он опоздал потому что был занят." → "Он опоздал, потому что был занят."
   - Do NOT split inside fixed compounds: "потому что" / "так как" /
     "несмотря на то что" are single conjunctions — never put a comma
     before "что" if it follows "потому"/"так как"/etc.

2) Participial phrases (ПРИЧАСТНЫЙ ОБОРОТ) AFTER the noun: commas
   on both sides (or one side if at clause boundary).
   - "Книга лежащая на столе принадлежит мне." →
     "Книга, лежащая на столе, принадлежит мне."
   - Do NOT flag if the participle is BEFORE the noun:
     "Лежащая на столе книга принадлежит мне." — correct, no commas.

3) Adverbial participles (ДЕЕПРИЧАСТНЫЙ ОБОРОТ): always commas.
   - "Войдя в комнату он увидел свет." → "Войдя в комнату, он увидел свет."
   - "Он шёл напевая песню." → "Он шёл, напевая песню."

4) Address (ОБРАЩЕНИЕ): commas around the addressee.
   - "Иван иди сюда." → "Иван, иди сюда."
   - "Расскажи мне Маша эту историю." → "Расскажи мне, Маша, эту историю."

5) Introductory words (ВВОДНЫЕ СЛОВА): конечно, к сожалению, например,
   по-моему, кажется, наверное — comma after (or around if mid-sentence).
   - "К сожалению я опоздал." → "К сожалению, я опоздал."
   - "Это конечно неправильно." → "Это, конечно, неправильно."
   - Do NOT confuse with the same word as an adverb: "Это, конечно, верно"
     (introductory, comma) vs "Он конечно знает дорогу" (adverb of certainty,
     no comma) — when in doubt, prefer the introductory reading only if the
     word is clearly parenthetical.

For ANY case not matching these five — leave it alone."""

# Ordered list of blocks contributed by this language module.
# The dispatcher inserts these after MODE_BLOCK and before the
# language-agnostic output / format blocks from `common`.
BLOCKS = [
    AGREEMENT_BLOCK,
    CASES_BLOCK,
    TSYA_TSIA_BLOCK,
    CONFUSABLES_BLOCK,
    COMMAS_BLOCK,
]
