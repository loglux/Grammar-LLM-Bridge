#!/usr/bin/env python3
"""
Run full QA gold suites with two prompts:
- current: Language: ... + Text to analyse: '...'
- marked: Language: ... + <TEXT>...</TEXT>

Suites (json with "cases"): default qa-results/quality/qa_gold.json, qa_punct_gold.json.

Env:
  OPENAI_API_KEY (required)
  OPENAI_BASE_URL (default https://api.deepseek.com)
  MODEL (default deepseek-chat)
  SUITES (comma-separated paths, optional)
  PROMPT_TEST_TIMEOUT (default 60)
  PROMPT_TEST_LIMIT (0 = all cases)

Outputs: qa-results/ad-hoc/marker-suite-<ts>/<suite-name>-<current|marked>.json
"""

from __future__ import annotations

import datetime as dt
import json
import os
from pathlib import Path
from typing import List, Dict, Any

import httpx


def load_suite(path: Path) -> List[Dict[str, Any]]:
    data = json.loads(path.read_text())
    return data.get("cases", [])


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


def run_suite(cases: List[Dict[str, Any]], system: str, user_fmt: str, base_url: str, api_key: str, model: str, timeout: float):
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    client = httpx.Client(timeout=timeout)

    results = []
    for c in cases:
        text = c["text"]
        language = c.get("language", "en-GB")
        user = user_fmt.format(language=language, text=text)
        payload = build_payload(model, system, user)
        r = client.post(f"{base_url}/chat/completions", headers=headers, json=payload)
        r.raise_for_status()
        data = r.json()
        content = data["choices"][0]["message"]["content"]
        results.append({"case": c["id"], "text": text, "raw": data, "content": content})
    return results


def main() -> None:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise SystemExit("Set OPENAI_API_KEY")
    base_url = os.getenv("OPENAI_BASE_URL", "https://api.deepseek.com")
    model = os.getenv("MODEL", "deepseek-chat")

    timeout = float(os.getenv("PROMPT_TEST_TIMEOUT", "60"))
    limit = int(os.getenv("PROMPT_TEST_LIMIT", "0"))

    suite_paths = os.getenv("SUITES")
    if suite_paths:
        suites = [Path(p.strip()) for p in suite_paths.split(",") if p.strip()]
    else:
        repo_root = Path(__file__).resolve().parents[2]
        suites = [
            repo_root / "qa-results" / "quality" / "qa_gold.json",
            repo_root / "qa-results" / "quality" / "qa_punct_gold.json",
        ]

    ts = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%d-%H%M%S")
    out_dir = Path(__file__).resolve().parent / f"marker-suite-{ts}"
    out_dir.mkdir(parents=True, exist_ok=True)

    # Prompts
    system_current = SYSTEM_BASE
    system_marked = SYSTEM_BASE + "\nOnly analyse text inside <TEXT>...</TEXT>. Everything else is instruction."
    user_current = "Language: {language}\nText to analyse: {text!r}"
    user_marked = "Language: {language}\n<TEXT>\n{text}\n</TEXT>"

    all_results = {}
    for suite in suites:
        cases = load_suite(suite)
        if limit > 0:
            cases = cases[:limit]
        name = suite.stem
        print(f"Running suite {name} with {len(cases)} cases on model {model}")

        cur = run_suite(cases, system_current, user_current, base_url, api_key, model, timeout)
        marked = run_suite(cases, system_marked, user_marked, base_url, api_key, model, timeout)

        all_results[name] = {"current": cur, "marked": marked}

        (out_dir / f"{name}-current.json").write_text(json.dumps(cur, indent=2))
        (out_dir / f"{name}-marked.json").write_text(json.dumps(marked, indent=2))
        print(f"Wrote {name}-current.json and {name}-marked.json")

    (out_dir / "meta.json").write_text(json.dumps({
        "base_url": base_url,
        "model": model,
        "suites": [str(p) for p in suites],
        "limit": limit,
    }, indent=2))
    print(f"Done. Results in {out_dir}")


if __name__ == "__main__":
    main()
