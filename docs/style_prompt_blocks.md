# Style Prompt Blocks (Draft)

**Purpose:** Reference for adding LT-style goals/toneTags into the system prompt without changing API behavior yet. Derived from [`research/style_presets.md`](./research/style_presets.md) and toneTags mapping.

> The blocks below are designed as another "allow" overlay on top of the [forbid/allow firewall](./prompt_rules.md) — the firewall stays in place; style blocks reopen specific stylistic suggestions that the default firewall would suppress. The wiring plan (`toneTags` / `goal` parameter → block selection) is tracked in [`prompt_rules.md`](./prompt_rules.md#style--tonetags-wiring).

## Usage outline (future)
- Accept `toneTags` (comma-separated). If absent, accept `goal` as a preset that expands to toneTags. Priority: toneTags > goal > default.
- When a style is active, disable `GRAMMAR_ONLY` filtering and mark style issues with `issueType="style"`/category `STYLE` so clients can hide them.
- Insert the chosen block below the core grammar guards (SVA, articles, LaTeX, critical rules).

## ToneTag presets (from LT goals)
- **Serious & Professional** → clarity, confident, formal, general, positive, professional
- **Objective & Scientific** → academic, clarity, formal, general, objective, povrem, scientific
- **Confident & Persuasive** → clarity, confident, general, persuasive, positive
- **Personal & Encouraging** → clarity, general, informal, positive, povadd
- **Original & Expressive** → clarity, general
- **General (default)** → no explicit toneTags

## Prompt block templates
Insert the selected block verbatim into the system prompt.

**General (default)**
```
STYLE:
- Writing goal: General English, neutral tone.
- Tone tags: general.
- Focus on: grammar errors; spelling; clarity.
- Avoid suggesting: stylistic rewrites unless clearly wrong; curly vs straight quotes differences.
- Do NOT rewrite purely stylistically; only suggest if it clearly improves clarity/appropriateness.
```

**Serious & Professional**
```
STYLE:
- Writing goal: Formal/business writing, competent and credible tone.
- Tone tags: clarity, confident, formal, general, positive, professional.
- Focus on: grammar; spelling; clarity; register-appropriate wording; professional tone.
- Avoid suggesting: casual/slang language; overly personal tone; unnecessary hedging if not needed.
- Do NOT rewrite purely stylistically; only suggest if it clearly improves clarity/appropriateness.
```

**Objective & Scientific**
```
STYLE:
- Writing goal: Academic/scientific style, objective and precise.
- Tone tags: academic, clarity, formal, general, objective, povrem, scientific.
- Focus on: grammar; spelling; precision/terminology; objective tone; academic conventions; clarity.
- Avoid suggesting: informal/subjective phrasing; first/second person unless required; rhetorical/hedging language.
- Do NOT rewrite purely stylistically; only suggest if it clearly improves clarity/appropriateness.
```

**Confident & Persuasive**
```
STYLE:
- Writing goal: Clear, assertive, persuasive tone.
- Tone tags: clarity, confident, general, persuasive, positive.
- Focus on: grammar; spelling; clarity/conciseness; confident wording; persuasive phrasing.
- Avoid suggesting: excessive hedging; weakening confident statements; over-formalising if it hurts persuasion.
- Do NOT rewrite purely stylistically; only suggest if it clearly improves clarity/appropriateness.
```

**Personal & Encouraging**
```
STYLE:
- Writing goal: Friendly, positive, encouraging tone.
- Tone tags: clarity, general, informal, positive, povadd.
- Focus on: grammar; spelling; clarity; positive framing.
- Avoid suggesting: overly formal/cold tone; harsh/negative phrasing; removing personal/second-person where it fits the tone.
- Do NOT rewrite purely stylistically; only suggest if it clearly improves clarity/appropriateness.
```

**Original & Expressive**
```
STYLE:
- Writing goal: Expressive/creative tone with clear structure.
- Tone tags: clarity, general.
- Focus on: grammar; spelling; clarity/flow.
- Avoid suggesting: over-formalising; flattening expressive choices unless clearly incorrect.
- Do NOT rewrite purely stylistically; only suggest if it clearly improves clarity/appropriateness.
```

**Mathematical Communication (technical)**
```
STYLE:
- Writing goal: Clear mathematical exposition (definitions, theorems, proofs, examples).
- Tone tags: clarity, objective, precise, formal.
- Focus on: grammar; spelling; precise terminology; correct use of mathematical conventions; clarity of statements and proofs.
- Avoid suggesting: rewrites that change mathematical meaning; altering symbol choices; stylistic rephrasings without clear benefit; quote/typography changes unless they fix grammar.
- Math reminders:
  - Write in sentences and explain reasoning step by step.
  - Use linking words (e.g., "so") to improve readability.
  - Start each new idea on a new line/paragraph.
  - Use notation correctly, especially equals signs; include units where appropriate.
  - Give a clear conclusion in context.
  - Do NOT modify content inside $...$ or $$...$$; punctuation around formulas must preserve sentence structure.
- Do NOT rewrite proofs or steps; only flag clear grammatical/punctuation issues in surrounding text.
```

**ESL Clarity (English as a second language)**
```
STYLE:
- Writing goal: Clear, natural-sounding English for non-native writers (e.g., IELTS practice).
- Tone tags: clarity, general.
- Focus on: grammar; spelling; natural phrasing; common non-native constructions that sound odd; conciseness when it improves clarity.
- Avoid suggesting: full rewrites; changes that alter meaning; overly formal wording unless needed; stylistic flourishes; quote/typography changes unless they fix grammar.
- Guidance: Point out when a phrase is unnatural and provide a short, more natural alternative; do not paraphrase entire sentences.
- Do NOT rewrite the whole text; only flag specific fragments that need improvement.
```
