#!/usr/bin/env python3
"""
Aggregate latency benchmark runs produced by latency_benchmark.py.

Reads qa-results/ad-hoc/latency-run-*/results.json and writes:
  - <prefix>-summary.{txt,json}
  - <prefix>-boxplot.png
  - <prefix>-ecdf.png
  - <prefix>-hist.png
  - <prefix>-rows-wide.csv (one row per trial: httpx_ms, sdk_ms)
  - <prefix>-rows-long.csv (one row per measurement: mode, latency_ms)

Optional filtering:
  - LATENCY_FILTER_BASE_URL: keep only runs whose results.json has matching base_url
  - LATENCY_FILTER_MODEL: keep only runs whose results.json has matching model
  - LATENCY_OUT_PREFIX: output file prefix (default: latency-ALL)

All outputs are written to qa-results/ad-hoc/.
"""

from __future__ import annotations

import json
import os
import statistics
from pathlib import Path
from typing import Any, Dict, List, Tuple

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns


def pct(values: List[float], p: float) -> float:
    if not values:
        return float("nan")
    s = sorted(values)
    k = (len(s) - 1) * p
    f = int(k)
    c = min(f + 1, len(s) - 1)
    if f == c:
        return s[f]
    return s[f] + (s[c] - s[f]) * (k - f)


def agg(values: List[float]) -> Dict[str, float]:
    return {
        "n": len(values),
        "mean": statistics.mean(values),
        "median": statistics.median(values),
        "stdev": statistics.pstdev(values) if len(values) > 1 else 0.0,
        "min": min(values),
        "p90": pct(values, 0.90),
        "p95": pct(values, 0.95),
        "max": max(values),
    }


def load_runs(base: Path) -> Tuple[List[Dict[str, Any]], List[Path]]:
    files = sorted(base.glob("latency-run-*/results.json"))
    rows: List[Dict[str, Any]] = []
    used: List[Path] = []

    filter_base_url = os.getenv("LATENCY_FILTER_BASE_URL")
    filter_model = os.getenv("LATENCY_FILTER_MODEL")

    for f in files:
        payload = json.loads(f.read_text())
        meta = payload.get("meta", {})
        base_url = meta.get("base_url")
        model = meta.get("model")
        if filter_base_url and base_url != filter_base_url:
            continue
        if filter_model and model != filter_model:
            continue

        for r in payload.get("rows", []):
            r = dict(r)
            r["run_dir"] = f.parent.name
            r["base_url"] = base_url
            r["model"] = model
            rows.append(r)
        used.append(f)

    return rows, used


def main() -> None:
    base = Path(__file__).resolve().parent
    rows, used = load_runs(base)
    if not rows:
        raise SystemExit("No matching runs found.")

    prefix = os.getenv("LATENCY_OUT_PREFIX", "latency-ALL")

    httpx_vals = [r["httpx_ms"] for r in rows]
    sdk_vals = [r["sdk_ms"] for r in rows]

    summary = {
        "httpx": agg(httpx_vals),
        "sdk": agg(sdk_vals),
        "runs": len(rows),
        "used_files": [str(p) for p in used],
        "filters": {
            "base_url": os.getenv("LATENCY_FILTER_BASE_URL"),
            "model": os.getenv("LATENCY_FILTER_MODEL"),
        },
    }

    (base / f"{prefix}-summary.json").write_text(json.dumps(summary, indent=2))
    with (base / f"{prefix}-summary.txt").open("w") as f:
        f.write("Combined latency summary (ms)\n")
        if summary["filters"]["base_url"] or summary["filters"]["model"]:
            f.write(f"Filters: {summary['filters']}\n")
        f.write(f"Total runs: {summary['runs']}\n\n")
        for mode in ("httpx", "sdk"):
            a = summary[mode]
            f.write(
                f"{mode}: n={a['n']}, mean={a['mean']:.1f}, median={a['median']:.1f}, "
                f"stdev={a['stdev']:.1f}, p90={a['p90']:.1f}, p95={a['p95']:.1f}, "
                f"min={a['min']:.1f}, max={a['max']:.1f}\n"
            )

    df = pd.DataFrame(
        [{"mode": "httpx", "latency_ms": v} for v in httpx_vals]
        + [{"mode": "sdk", "latency_ms": v} for v in sdk_vals]
    )

    # Raw rows as CSV (wide and long)
    wide_rows = [
        {
            "run_dir": r.get("run_dir"),
            "base_url": r.get("base_url"),
            "model": r.get("model"),
            "trial": r.get("run"),
            "httpx_ms": r.get("httpx_ms"),
            "sdk_ms": r.get("sdk_ms"),
        }
        for r in rows
    ]
    pd.DataFrame(wide_rows).to_csv(base / f"{prefix}-rows-wide.csv", index=False)
    df.to_csv(base / f"{prefix}-rows-long.csv", index=False)

    # Boxplot
    plt.figure(figsize=(6, 4))
    sns.boxplot(data=df, x="mode", y="latency_ms")
    sns.stripplot(data=df, x="mode", y="latency_ms", color="black", alpha=0.35)
    plt.title("Latency (all runs)")
    plt.tight_layout()
    plt.savefig(base / f"{prefix}-boxplot.png", dpi=200)
    plt.close()

    # ECDF
    plt.figure(figsize=(6, 4))
    sns.ecdfplot(data=df, x="latency_ms", hue="mode")
    plt.title("Latency ECDF (all runs)")
    plt.xlabel("latency (ms)")
    plt.tight_layout()
    plt.savefig(base / f"{prefix}-ecdf.png", dpi=200)
    plt.close()

    # Histogram
    plt.figure(figsize=(6, 4))
    sns.histplot(data=df, x="latency_ms", hue="mode", bins=20, element="step", stat="density", common_norm=False)
    plt.title("Latency distribution (all runs)")
    plt.xlabel("latency (ms)")
    plt.tight_layout()
    plt.savefig(base / f"{prefix}-hist.png", dpi=200)
    plt.close()

    print("Wrote:")
    print(f"- {base / f'{prefix}-summary.txt'}")
    print(f"- {base / f'{prefix}-boxplot.png'}")
    print(f"- {base / f'{prefix}-ecdf.png'}")
    print(f"- {base / f'{prefix}-hist.png'}")
    print(f"- {base / f'{prefix}-rows-wide.csv'}")
    print(f"- {base / f'{prefix}-rows-long.csv'}")


if __name__ == "__main__":
    main()
