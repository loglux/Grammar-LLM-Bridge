# Style Presets

## Purpose
- Consolidated local notes on writing goals/style context (LT goal/toneTags), to avoid confusion.
- Not part of repo; for implementation reference only.

## Parameters / Priorities
- Accept `goal` (enum from LT goals) and optional `toneTags` (comma-separated).
- Priority: toneTags > goal > default.
- Default (no goal/toneTags): use General style block; toneTags not sent.

## Goal → toneTags (LT reference: dev.languagetool.org/style_tone_tags)
- Serious & Professional → clarity, confident, formal, general, positive, professional
- Objective & Scientific → academic, clarity, formal, general, objective, povrem, scientific
- Confident & Persuasive → clarity, confident, general, persuasive, positive
- Personal & Encouraging → clarity, general, informal, positive, povadd
- Original & Expressive → clarity, general
- General → [] (no explicit toneTags)

## Style configs (for prompt blocks)
```
STYLE_CONFIGS = {
    "general": {
        "description": "General English, neutral tone",
        "focus_on": ["grammar errors", "spelling", "clarity"],
        "avoid_suggesting": [
            "over-correcting style",
            "differences in curly vs straight quotes unless grammar error"
        ]
    },
    "serious_professional": {
        "description": "Formal/business writing, competent and credible tone",
        "focus_on": ["grammar", "spelling", "clarity", "formal/register-appropriate wording", "professional tone"],
        "avoid_suggesting": [
            "casual/slang language",
            "overly personal tone",
            "unnecessary hedging if not needed"
        ]
    },
    "objective_scientific": {
        "description": "Academic/scientific style, objective and precise",
        "focus_on": ["grammar", "spelling", "precision/terminology", "objective tone", "academic conventions", "clarity"],
        "avoid_suggesting": [
            "informal/subjective phrasing",
            "first/second person unless required",
            "rhetorical/hedging language"
        ]
    },
    "confident_persuasive": {
        "description": "Clear, assertive, persuasive tone",
        "focus_on": ["grammar", "spelling", "clarity/conciseness", "confident wording", "persuasive phrasing"],
        "avoid_suggesting": [
            "excessive hedging",
            "weakening confident statements",
            "over-formalising if it hurts persuasion"
        ]
    },
    "personal_encouraging": {
        "description": "Friendly, positive, encouraging tone",
        "focus_on": ["grammar", "spelling", "clarity", "positive framing"],
        "avoid_suggesting": [
            "overly formal/cold tone",
            "harsh/negative phrasing",
            "removing personal/second-person where it fits the tone"
        ]
    },
    "original_expressive": {
        "description": "Expressive/creative tone with clear structure",
        "focus_on": ["grammar", "spelling", "clarity/flow"],
        "avoid_suggesting": [
            "over-formalising",
            "flattening expressive choices unless clearly incorrect"
        ]
    }
}
```

## Prompt usage (to implement)
- Build style block from config; insert into ALL prompts (schema/json_object/fallback).
- Default: General block; toneTags not sent; optionally keep GRAMMAR_ONLY=true for pure grammar.
- With goal/toneTags: build block from chosen style; set GRAMMAR_ONLY=false; keep other guards.

## Filters (current, summarized)
- No-op (replacement == error_text).
- LaTeX mask ($...$, $$...$$).
- Redundant article guard.
- Capital-letter off-boundary guard.
- Leading punctuation guard.
- Trailing punctuation guard (`, . ; : ! ?`).
- Single-token expansion guard (drop expansion like "hangs" -> "hangs loose").
- GRAMMAR_ONLY: drop style keys except punctuation/comma (when true).

## Notes
- Do not commit this file; for local reference.
- Source for toneTags/goal mapping: dev.languagetool.org/style_tone_tags.
