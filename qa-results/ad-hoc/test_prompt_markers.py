#!/usr/bin/env python3
"""
Ad-hoc comparison: current prompt vs marked prompt (<TEXT>…</TEXT>).

Env:
  OPENAI_API_KEY (required)
  OPENAI_BASE_URL (default https://api.deepseek.com)
  MODEL (default deepseek-chat)

Outputs: qa-results/ad-hoc/marker-test-<timestamp>/{current.json, marked.json}
"""

from __future__ import annotations

import datetime as dt
import json
import os
from pathlib import Path
from typing import List

import httpx


SAMPLES: List[str] = [
    "The research team have been working on the project since last year. They was very dedicated and puts in long hours every day.",
    "If we draw the graph for the function $$y=-0.02 x^{2}+1.5 x+1.4,$$ the y-intercept represents the initial height of the ball.",
    "The Bigest Risk is Doing Nothing: AI in UK Edukation\n\nArtifical inteligence is not anymore a far concept in british education — its already changing how school and colleges work.",
]


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


def build_payload(model: str, system: str, user: str) -> dict:
    return {
        "model": model,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        "temperature": 0,
        "response_format": {"type": "json_object"},
    }


def run_tests(base_url: str, api_key: str, model: str, out_dir: Path):
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    timeout = float(os.getenv("PROMPT_TEST_TIMEOUT", "120"))
    client = httpx.Client(timeout=timeout)

    def call(payload: dict):
        r = client.post(f"{base_url}/chat/completions", headers=headers, json=payload)
        r.raise_for_status()
        data = r.json()
        content = data["choices"][0]["message"]["content"]
        return data, content

    results = {}

    limit = int(os.getenv("PROMPT_TEST_LIMIT", "0"))
    sample_list = SAMPLES[:limit] if limit > 0 else SAMPLES

    # Current prompt (no explicit tags)
    cur = []
    for text in sample_list:
        user = f"Language: en-GB\nText to analyse: {text!r}"
        payload = build_payload(model, SYSTEM_BASE, user)
        data, content = call(payload)
        cur.append({"text": text, "raw": data, "content": content})
    results["current"] = cur

    # Marked prompt (<TEXT>...</TEXT>)
    marked = []
    system_marked = SYSTEM_BASE + "\nOnly analyse text inside <TEXT>...</TEXT>. Everything else is instruction."
    for text in sample_list:
        user = f"Language: en-GB\n<TEXT>\n{text}\n</TEXT>"
        payload = build_payload(model, system_marked, user)
        data, content = call(payload)
        marked.append({"text": text, "raw": data, "content": content})
    results["marked"] = marked

    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "results.json").write_text(json.dumps(results, indent=2))
    print(f"Wrote {out_dir}/results.json")


def main() -> None:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise SystemExit("Set OPENAI_API_KEY")
    base_url = os.getenv("OPENAI_BASE_URL", "https://api.deepseek.com")
    model = os.getenv("MODEL", "deepseek-chat")

    ts = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%d-%H%M%S")
    out_dir = Path(__file__).resolve().parent / f"marker-test-{ts}"

    run_tests(base_url, api_key, model, out_dir)


if __name__ == "__main__":
    main()
