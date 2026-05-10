#!/usr/bin/env python3
"""
Latency benchmark: httpx vs OpenAI Python SDK.

Runs sequential requests and produces raw data + per-run plots.
Aggregate across multiple runs with latency_aggregate.py.

Env:
  - OPENAI_API_KEY (required)
  - OPENAI_BASE_URL (optional; default https://api.deepseek.com)
  - LLM_MODEL (optional; default deepseek-chat)
  - LATENCY_RUNS (optional; default 10)

Outputs:
  qa-results/ad-hoc/latency-run-<timestamp>/{results.json,summary.txt,latency_boxplot.png}
"""

from __future__ import annotations

import datetime as dt
import json
import os
import statistics
import time
from pathlib import Path
from typing import Dict, List

import httpx
import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns
from openai import OpenAI


def _normalize_base_url(base_url: str) -> str:
    base = base_url.rstrip("/")
    if base.endswith("/v1"):
        return base
    return base + "/v1"


def call_httpx(base_url: str, api_key: str, payload: dict) -> float:
    url = f"{_normalize_base_url(base_url)}/chat/completions"
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    t0 = time.perf_counter()
    with httpx.Client(timeout=60.0) as client:
        resp = client.post(url, headers=headers, json=payload)
        resp.raise_for_status()
    return (time.perf_counter() - t0) * 1000.0  # ms


def call_sdk(base_url: str, api_key: str, payload: dict) -> float:
    client = OpenAI(api_key=api_key, base_url=_normalize_base_url(base_url))
    t0 = time.perf_counter()
    client.chat.completions.create(**payload)
    return (time.perf_counter() - t0) * 1000.0  # ms


def run_once(base_url: str, api_key: str, payload: dict) -> Dict[str, float]:
    return {
        "httpx_ms": call_httpx(base_url, api_key, payload),
        "sdk_ms": call_sdk(base_url, api_key, payload),
    }


def aggregate(values: List[float]) -> Dict[str, float]:
    return {
        "n": len(values),
        "mean": statistics.mean(values),
        "median": statistics.median(values),
        "stdev": statistics.pstdev(values) if len(values) > 1 else 0.0,
        "min": min(values),
        "max": max(values),
    }


def main() -> None:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise SystemExit("Set OPENAI_API_KEY")
    base_url = os.getenv("OPENAI_BASE_URL", "https://api.deepseek.com")
    model = os.getenv("LLM_MODEL", "deepseek-chat")

    user_text = (
        "Language: en-GB\n"
        "Text to analyse: 'The research team have been working on the project since last year. "
        "They was very dedicated and puts in long hours every day. "
        "The results shows that the hypothesis were correct and the data confirm our predictions.'"
    )
    payload = {
        "model": model,
        "messages": [
            {
                "role": "system",
                "content": (
                    "You are a strict grammar checker. Return only a JSON array of issues. "
                    "Each item must include message, error_text, and replacements (array of strings). "
                    "If no errors, return []."
                ),
            },
            {"role": "user", "content": user_text},
        ],
        "temperature": 0,
        # DeepSeek expects json_object; OpenAI supports it too (we only benchmark latency here).
        "response_format": {"type": "json_object"},
    }

    run_id = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%d-%H%M%S")
    out_dir = Path(__file__).resolve().parent / f"latency-run-{run_id}"
    out_dir.mkdir(parents=True, exist_ok=True)

    httpx_samples: List[float] = []
    sdk_samples: List[float] = []
    rows = []

    iterations = int(os.getenv("LATENCY_RUNS", "10"))
    for i in range(1, iterations + 1):
        timings = run_once(base_url, api_key, payload)
        httpx_samples.append(timings["httpx_ms"])
        sdk_samples.append(timings["sdk_ms"])
        rows.append({"run": i, **timings})
        print(f"Run {i}: httpx={timings['httpx_ms']:.1f} ms, sdk={timings['sdk_ms']:.1f} ms")

    stats = {
        "httpx": aggregate(httpx_samples),
        "sdk": aggregate(sdk_samples),
        "runs": iterations,
    }

    # Save raw data and stats
    with (out_dir / "results.json").open("w") as f:
        json.dump(
            {
                "meta": {
                    "base_url": base_url,
                    "model": model,
                    "runs": iterations,
                },
                "rows": rows,
                "stats": stats,
            },
            f,
            indent=2,
        )

    # Boxplot
    df = pd.DataFrame(
        [{"mode": "httpx", "latency_ms": v} for v in httpx_samples]
        + [{"mode": "sdk", "latency_ms": v} for v in sdk_samples]
    )
    plt.figure(figsize=(6, 4))
    sns.boxplot(data=df, x="mode", y="latency_ms")
    sns.stripplot(data=df, x="mode", y="latency_ms", color="black", alpha=0.6)
    plt.title("DeepSeek latency (ms)")
    plt.tight_layout()
    plt.savefig(out_dir / "latency_boxplot.png", dpi=200)

    # Text report
    with (out_dir / "summary.txt").open("w") as f:
        f.write("Latency benchmark (ms)\n")
        f.write(f"Base URL: {base_url}\nRuns: {iterations}\n\n")
        for mode, agg in stats.items():
            if mode == "runs":
                continue
            f.write(f"{mode}:\n")
            f.write(
                f"  mean={agg['mean']:.1f}, median={agg['median']:.1f}, "
                f"stdev={agg['stdev']:.1f}, min={agg['min']:.1f}, max={agg['max']:.1f}\n"
            )

    print(f"\nSaved results to: {out_dir}")


if __name__ == "__main__":
    main()
