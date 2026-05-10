# Style Configs for LT Goals (Plan)

Goal -> config (description, focus_on, avoid_suggesting), derived from dev.languagetool.org/style_tone_tags.

## general (default, if no goal/tags)
- description: General English, neutral tone.
- focus_on: grammar errors; spelling; clarity.
- avoid_suggesting: style rewrites unless clearly wrong; curly vs straight quotes differences.

## serious_professional (Serious & Professional)
- description: Formal/business writing, competent and credible tone.
- focus_on: grammar; spelling; clarity; formal/register-appropriate wording; professionalism.
- avoid_suggesting: casual/slang; overly personal tone; unnecessary softening/hedging if not needed.

## objective_scientific (Objective & Scientific)
- description: Academic/scientific style, objective and precise.
- focus_on: grammar; spelling; precision/terminology; objective tone; academic conventions; clarity.
- avoid_suggesting: informal/subjective phrasing; first/second person (unless required); rhetorical/hedging language.

## confident_persuasive (Confident & Persuasive)
- description: Clear, assertive, persuasive tone.
- focus_on: grammar; spelling; clarity/conciseness; confident wording; persuasive phrasing.
- avoid_suggesting: excessive hedging; weakening confident statements; over-formalising if it hurts persuasion.

## personal_encouraging (Personal & Encouraging)
- description: Friendly, positive, encouraging tone.
- focus_on: grammar; spelling; clarity; positive framing.
- avoid_suggesting: overly formal/cold tone; harsh/negative phrasing; removing personal/second-person where it fits the tone.

## original_expressive (Original & Expressive)
- description: Expressive/creative tone with clear structure.
- focus_on: grammar; spelling; clarity/flow.
- avoid_suggesting: over-formalising; flattening expressive choices unless clearly incorrect.

Notes:
- These configs are for prompt-building; goal → toneTags mapping is as per LT (see STYLE_GOALS_PLAN_LOCAL.md). This file only sketches descriptions/focus/avoid.
- Not implemented yet; meant for future parametric prompts (schema/json_object/fallback).
