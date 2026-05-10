#!/usr/bin/env python3
"""
Quick AB test for long text:
- send whole text vs chunked-by-paragraph
- optional max_tokens override
- print latency and whether JSON parsed
"""

import os
import time
import json
import httpx
from textwrap import dedent


TEXT = dedent(
    """Dotplots would show the real data values for each individual data. We could see the particular values and how they occur. They show not only the spread but also the form of the spread, where we could see some bunching of data to one side or they are symmetrical and where there are clear outliers. If the particular value occurs many times, it would be visible by the height of the stack of dots, while in boxplots the details of frequencies are lost and dotplots don't provide the visibility of the context.

We could see there not only the fact that Group A is overall slower than Group B but also spot the wider spread in the Group A, and that Group B shows better stability and the concentration around the centre."""
).strip()


def build_payload(text: str, max_tokens: int | None = None) -> dict:
    prompt = (
        "You are a grammar checker. Return a JSON array of issues, each with fields: "
        "message, error_text, replacements (array of strings). "
        "Return ONLY JSON (no markdown). Copy error_text exactly from input.\n\n"
        f"Text: {text}"
    )
    payload = {
        "model": os.environ.get("LLM_MODEL", "deepseek-chat"),
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0,
    }
    if max_tokens:
        payload["max_tokens"] = max_tokens
    return payload


def call(payload: dict, base_url: str, api_key: str) -> tuple[bool, float, str]:
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    url = f"{base_url}/chat/completions"
    t0 = time.time()
    with httpx.Client(timeout=60.0) as client:
        r = client.post(url, headers=headers, json=payload)
    dt = (time.time() - t0) * 1000
    try:
        content = r.json()["choices"][0]["message"]["content"]
        ok = True
    except Exception as e:
        content = f"parse_error: {e}; body[:200]={r.text[:200]}"
        ok = False
    return ok, dt, content


def run_case(label: str, texts: list[str], max_tokens: int | None, base_url: str, api_key: str):
    total_ms = 0
    all_ok = True
    parts = []
    for i, t in enumerate(texts, 1):
        payload = build_payload(t, max_tokens=max_tokens)
        ok, ms, content = call(payload, base_url, api_key)
        total_ms += ms
        all_ok = all_ok and ok
        parts.append({"part": i, "ok": ok, "ms": ms, "preview": content[:200]})
    print(f"\n=== {label} ===")
    print(f"parts: {len(texts)}, total_ms={total_ms:.1f}, all_ok={all_ok}")
    for p in parts:
        print(f" part {p['part']}: ok={p['ok']} ms={p['ms']:.1f} preview={p['preview']}")


def main():
    api_key = os.getenv("OPENAI_API_KEY")
    base_url = os.getenv("OPENAI_BASE_URL", "https://api.deepseek.com")
    if not api_key:
        raise SystemExit("Set OPENAI_API_KEY")

    paragraphs = [p.strip() for p in TEXT.split("\n\n") if p.strip()]

    run_case("whole_default", [TEXT], None, base_url, api_key)
    run_case("whole_max8000", [TEXT], 8000, base_url, api_key)
    run_case("chunks_default", paragraphs, None, base_url, api_key)
    run_case("chunks_max8000", paragraphs, 8000, base_url, api_key)


if __name__ == "__main__":
    main()
