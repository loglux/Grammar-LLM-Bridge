#!/usr/bin/env python3
"""
Run qa_gold / qa_punct_gold with two system prompts:
- baseline (current system prompt)
- sva (baseline + subject-verb agreement examples)

Env:
  OPENAI_API_KEY (required)
  OPENAI_BASE_URL (default https://api.deepseek.com)
  MODEL (default deepseek-chat)
  PROMPT_TEST_TIMEOUT (default 60)
  PROMPT_TEST_LIMIT (0 = all cases)
"""

from __future__ import annotations

import datetime as dt
import json
import os
from pathlib import Path
from typing import Dict, Any, List

import httpx

ROOT = Path(__file__).resolve().parents[2]
QUALITY = ROOT / "qa-results" / "quality"


def load_cases(path: Path) -> List[Dict[str, Any]]:
    data = json.loads(path.read_text())
    return data.get("cases", [])


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


SYSTEM_SVA_BLOCK = """
SUBJECT–VERB AGREEMENT (AVOID FALSE POSITIVES):
- The subject is not the nearest plural noun. Analyse the whole phrase.
- GOOD: "The list of new items is long." → subject = list (singular), DO NOT change "is".
- GOOD: "A key feature of these models is their speed." → subject = feature (singular), DO NOT change "is".
- BAD: "The items in the list is long." → subject = items (plural), MUST change "is"→"are".
- GOOD: "The horses runs fast." → flag "runs" → ["run"].
- BAD: "The list of approved items, which contains many entries, is now final." → DO NOT flag "is".
"""


def build_payload(model: str, system: str, language: str, text: str) -> dict:
    user = f"Language: {language}\nText to analyse: {text!r}"
    return {
        "model": model,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        "temperature": 0,
        "response_format": {"type": "json_object"},
    }


def run_cases(cases: List[Dict[str, Any]], system: str, base_url: str, api_key: str, model: str, timeout: float):
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    results = []
    with httpx.Client(timeout=timeout) as client:
        for c in cases:
            payload = build_payload(model, system, c.get("language", "en-GB"), c["text"])
            r = client.post(f"{base_url}/chat/completions", headers=headers, json=payload)
            r.raise_for_status()
            data = r.json()
            content = data["choices"][0]["message"]["content"]
            results.append({"case": c["id"], "text": c["text"], "raw": data, "content": content})
    return results


def main() -> None:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise SystemExit("Set OPENAI_API_KEY")
    base_url = os.getenv("OPENAI_BASE_URL", "https://api.deepseek.com")
    model = os.getenv("MODEL", "deepseek-chat")
    timeout = float(os.getenv("PROMPT_TEST_TIMEOUT", "60"))
    limit = int(os.getenv("PROMPT_TEST_LIMIT", "0"))

    suites_env = os.getenv("SUITES")
    if suites_env:
        suites = [Path(p.strip()) for p in suites_env.split(",") if p.strip()]
    else:
        suites = [
            QUALITY / "qa_gold.json",
            QUALITY / "qa_punct_gold.json",
        ]

    ts = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%d-%H%M%S")
    out_dir = ROOT / "qa-results" / "ad-hoc" / f"sva-ab-{ts}"
    out_dir.mkdir(parents=True, exist_ok=True)

    system_baseline = SYSTEM_BASE
    system_sva = SYSTEM_BASE + SYSTEM_SVA_BLOCK

    meta = {
        "base_url": base_url,
        "model": model,
        "timeout": timeout,
        "limit": limit,
    }
    (out_dir / "meta.json").write_text(json.dumps(meta, indent=2))

    for suite in suites:
        cases = load_cases(suite)
        if limit > 0:
            cases = cases[:limit]
        name = suite.stem
        print(f"Running suite {name} ({len(cases)} cases) model={model}")
        base_res = run_cases(cases, system_baseline, base_url, api_key, model, timeout)
        sva_res = run_cases(cases, system_sva, base_url, api_key, model, timeout)
        (out_dir / f"{name}-baseline.json").write_text(json.dumps(base_res, indent=2))
        (out_dir / f"{name}-sva.json").write_text(json.dumps(sva_res, indent=2))
        print(f"Wrote {name}-baseline.json and {name}-sva.json")

    print("Done. Results in", out_dir)


if __name__ == "__main__":
    main()
