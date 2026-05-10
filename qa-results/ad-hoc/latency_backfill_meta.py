#!/usr/bin/env python3
"""
Backfill `meta` into older latency-run-*/results.json files created before meta existed.

Strategy:
- If results.json already has "meta", leave it unchanged.
- Otherwise, parse `summary.txt` in the same run directory to extract "Base URL:" and "Runs:".
- Set:
    meta.base_url  -> parsed Base URL
    meta.runs      -> parsed Runs
    meta.model     -> best-effort:
        - if base_url contains "deepseek" -> "deepseek-chat"
        - if base_url contains "api.openai.com" -> "unknown"
        - else -> "unknown"

This is intended for local QA artefacts only.
"""

from __future__ import annotations

import json
import re
from pathlib import Path


def parse_summary(path: Path) -> tuple[str | None, int | None]:
    if not path.exists():
        return None, None
    text = path.read_text(errors="replace")
    m_url = re.search(r"^Base URL:\s*(.+)\s*$", text, re.MULTILINE)
    m_runs = re.search(r"^Runs:\s*(\d+)\s*$", text, re.MULTILINE)
    base_url = m_url.group(1).strip() if m_url else None
    runs = int(m_runs.group(1)) if m_runs else None
    return base_url, runs


def infer_model(base_url: str | None) -> str:
    if not base_url:
        return "unknown"
    if "deepseek" in base_url:
        return "deepseek-chat"
    if "api.openai.com" in base_url:
        return "unknown"
    return "unknown"


def main() -> None:
    base = Path(__file__).resolve().parent
    run_dirs = sorted([p for p in base.glob("latency-run-*") if p.is_dir()])
    changed = 0
    skipped = 0

    for d in run_dirs:
        results_path = d / "results.json"
        if not results_path.exists():
            continue
        payload = json.loads(results_path.read_text())
        if "meta" in payload and isinstance(payload["meta"], dict):
            skipped += 1
            continue

        base_url, runs = parse_summary(d / "summary.txt")
        payload["meta"] = {
            "base_url": base_url,
            "model": infer_model(base_url),
            "runs": runs if runs is not None else len(payload.get("rows", [])),
        }
        results_path.write_text(json.dumps(payload, indent=2))
        changed += 1

    print(f"Backfilled meta in {changed} runs; skipped {skipped} already-having-meta.")


if __name__ == "__main__":
    main()

