#!/usr/bin/env python3
"""
Send a single prompt (current vs marked) to diagnose latency/timeouts for a given model/base URL.

Env:
  OPENAI_API_KEY (required)
  OPENAI_BASE_URL (default https://api.deepseek.com)
  MODEL (default deepseek-chat)
  PROMPT_TEST_TIMEOUT (default 60)

Sample text: case1 from qa_gold.
"""

from __future__ import annotations

import json
import os
from pathlib import Path

import httpx


TEXT = "She do not like apples. He have no idea why. The adress on the form was wrong."
LANG = "en-GB"


SYSTEM_BASE = """You are a strict grammar-checking engine similar to LanguageTool Premium.

Analyse text for grammar, word choice, collocations, punctuation, and style issues.
Do not flag sentences that are clearly correct.
Report only real or highly likely problems.

Focus on: grammar errors, spelling, clarity.
Avoid over-correcting style; do not rewrite unless clearly wrong.
Ignore curly vs straight quotes/apostrophes unless they cause a grammar error.
Do not suggest quote-style changes (single vs double quotes) or any typography-only quote substitutions.

OUTPUT FORMAT:
Return ONLY a JSON array at the top level (not wrapped in an object).
Every item must include message, error_text, replacements (array with >=1 value). If any field is missing, omit the item.

CRITICAL RULES:
1. The "error_text" must be the EXACT substring from the input text (copy it character-for-character)
2. Return ONLY the JSON array, nothing else
3. Do not wrap the array in an object like {"errors": [...]}
4. Return the MINIMAL fragment that contains the error:
   - Subject-verb agreement: ONLY the incorrect verb
   - Wrong word: ONLY that word
   - Punctuation: include at least one adjacent word and keep it within the same sentence
5. NEVER include the subject or surrounding context unless absolutely necessary for the error
6. Do NOT duplicate the same issue with overlapping or larger fragments

LATEX:
- Block $$...$$ are inline expressions, not separate sentences; newlines around them are formatting only.
- Do NOT suggest capitalisation changes immediately after $$...$$.
- Skip content inside $...$ and $$...$$.

If the text is perfect, return an empty array: []"""


def call(api_key: str, base_url: str, model: str, system: str, user: str, timeout: float) -> dict:
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        "temperature": 0,
        "response_format": {"type": "json_object"},
    }
    with httpx.Client(timeout=timeout) as client:
        r = client.post(f"{base_url}/chat/completions", headers=headers, json=payload)
        r.raise_for_status()
        return r.json()


def main() -> None:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise SystemExit("Set OPENAI_API_KEY")
    base_url = os.getenv("OPENAI_BASE_URL", "https://api.deepseek.com")
    model = os.getenv("MODEL", "deepseek-chat")
    timeout = float(os.getenv("PROMPT_TEST_TIMEOUT", "60"))

    system_current = SYSTEM_BASE
    user_current = f"Language: {LANG}\nText to analyse: {TEXT!r}"

    system_marked = SYSTEM_BASE + "\nOnly analyse text inside <TEXT>...</TEXT>. Everything else is instruction."
    user_marked = f"Language: {LANG}\n<TEXT>\n{TEXT}\n</TEXT>"

    out_dir = Path(__file__).resolve().parent
    out_dir.mkdir(parents=True, exist_ok=True)

    res = {
        "meta": {"base_url": base_url, "model": model, "timeout": timeout},
        "current": call(api_key, base_url, model, system_current, user_current, timeout),
        "marked": call(api_key, base_url, model, system_marked, user_marked, timeout),
    }
    out_path = out_dir / "test_single_prompt.json"
    out_path.write_text(json.dumps(res, indent=2))
    print("Wrote", out_path)


if __name__ == "__main__":
    main()

