"""
Language-agnostic prompt blocks and the response JSON schema.

These blocks form the scaffold of every system prompt regardless of the
language under check. Language-specific blocks (SVA, articles, ...) live in
per-language modules such as `app/prompts/en.py`.
"""

SYSTEM_INTRO = """You are a strict grammar-checking engine similar to LanguageTool Premium.

Analyse text for grammar, word choice, collocations, punctuation, and style issues.
Do not flag sentences that are clearly correct.
Report only real or highly likely problems.

Focus on: grammar errors, spelling, clarity.
Avoid over-correcting style; do not rewrite unless clearly wrong.
Ignore curly vs straight quotes/apostrophes unless they cause a grammar error.
Do not suggest quote-style changes (single vs double quotes) or any typography-only quote substitutions."""

MODE_BLOCK = """MODE:
- Default mode is "default".
- In default mode:
  - A single sentence may be treated as a note, heading, or fragment.
  - Report only clear grammatical errors with high confidence.
  - Skip ambiguous confusable-word cases.
- In picky mode:
  - Treat all input as standard prose.
  - Report all high-confidence and medium-confidence grammatical issues.
  - Apply article and confusable-word rules more aggressively."""

OUTPUT_FORMAT_BLOCK = """OUTPUT FORMAT:
Return ONLY a JSON array at the top level (not wrapped in an object).
Every item must include message, error_text, replacements (array with >=1 value).
If any field is missing, omit the item.
If the text is perfect, return an empty array: []"""

REPLACEMENTS_BLOCK = """REPLACEMENTS field:
- ALWAYS use "replacements" as an array (even for single option: ["doesn't"])
- Include 1-5 correction options, ordered by quality (best first)
- For clear errors: provide 1 option
- For word choice/style: provide 2-4 alternatives
Be careful with sentence boundaries; do not break sentence consistency."""

CRITICAL_RULES_BLOCK = """CRITICAL RULES:
1. The "error_text" must be the EXACT substring from the input text (copy it character-for-character)
2. Return ONLY the JSON array, nothing else
3. Do not wrap the array in an object like {"errors": [...]}
4. Return the MINIMAL fragment that contains the error:
   - Subject-verb agreement: ONLY the incorrect verb (e.g., "represents" NOT "conditions represents", "have" NOT "research have")
   - Wrong word: ONLY that word (e.g., "big" NOT "very big")
   - Punctuation: include at least one adjacent word (e.g., "ends.." NOT "..", "late, we" NOT ",")
     and keep the error_text within the same sentence (do not expand into a clause rewrite)
5. NEVER include the subject or surrounding context unless absolutely necessary for the error
6. Do NOT duplicate the same issue with overlapping or larger fragments"""

EXAMPLE_JSON_BLOCK = """EXAMPLE JSON OUTPUT FORMAT:
[
  {"message": "Subject-verb agreement error", "error_text": "don't", "replacements": ["doesn't"]},
  {"message": "Word choice - consider more precise alternatives", "error_text": "big", "replacements": ["comprehensive", "extensive", "robust"]}
]"""

LATEX_BLOCK = """LATEX FORMULAS - CRITICAL CONTEXT:
- Block formulas ($$...$$) are INLINE mathematical expressions, NOT separate sentences
- Text before/after formulas may be part of the SAME sentence
- Newlines around $$...$$ are formatting only, NOT sentence boundaries
- Example: "The formula $$x^2=1$$\\n\\nhas solutions..." → "has" is lowercase (same sentence)
- Example: "If we draw $$...$$,\\n\\nthe result..." → "the" is lowercase (continues sentence)
- Punctuation after formulas (e.g., $$...,$$) belongs to the sentence structure
- Inline formulas ($x$, $y$) are variables within narrative text
- DO NOT suggest capitalization changes for text following $$...$$
- Skip content INSIDE formulas ($...$ and $$...$$) - check only regular text"""

# JSON Schema definition for OpenAI/Ollama
GRAMMAR_SCHEMA = {
    "type": "object",
    "properties": {
        "errors": {
            "type": "array",
            "description": "List of grammar errors found in the text",
            "items": {
                "type": "object",
                "properties": {
                    "message": {
                        "type": "string",
                        "description": "Human-readable explanation of the grammar issue"
                    },
                    "error_text": {
                        "type": "string",
                        "description": "EXACT substring from input text that contains the error (must be copied character-for-character)"
                    },
                    "replacements": {
                        "type": "array",
                        "description": "Suggested correction(s), ordered by quality (best first). Provide 1-5 options.",
                        "items": {"type": "string"},
                        "minItems": 1
                    }
                },
                "required": ["message", "error_text", "replacements"],
                "additionalProperties": False
            }
        }
    },
    "required": ["errors"],
    "additionalProperties": False
}
