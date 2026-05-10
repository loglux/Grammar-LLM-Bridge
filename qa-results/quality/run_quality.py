"""
Run a small gold-set quality check against the local Grammar-LLM-Bridge.
Writes per-case responses and a summary report.

Requirements: python3 (stdlib only). Endpoint: http://localhost:9019/v2/check
"""

import json
import pathlib
import time
import urllib.request
import os
import argparse
from statistics import mean

BASE = pathlib.Path(__file__).resolve().parent
DEFAULT_GOLD = BASE / "qa_gold.json"
SMOKE_GOLD = BASE / "gold_smoke.json"
CORE_GOLD = BASE / "gold_core.json"
LATEX_GOLD = BASE / "latex/no_hint.raw.json"  # placeholder if needed
ENDPOINT = "http://localhost:9019/v2/check"


def post_check(text: str, language: str, timeout: float = 30.0) -> tuple[int, str, float]:
    payload = json.dumps({"text": text, "language": language}).encode("utf-8")
    req = urllib.request.Request(
        ENDPOINT,
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    t0 = time.time()
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        status = resp.status
        body = resp.read().decode("utf-8")
    latency_ms = (time.time() - t0) * 1000.0
    return status, body, latency_ms


def normalise_replacements(repls_raw) -> list[str]:
    repls: list[str] = []
    for r in repls_raw or []:
        if isinstance(r, dict):
            repls.append(r.get("value"))
        elif isinstance(r, str):
            repls.append(r)
        else:
            repls.append(None)
    return [r for r in repls if r]

def _matches_error_text(candidate: str, expected: dict) -> bool:
    if candidate == expected.get("error_text"):
        return True
    alts = expected.get("error_text_alt") or []
    return candidate in alts


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--endpoint", default=ENDPOINT, help="Check endpoint")
    parser.add_argument(
        "--suite",
        default="core",
        choices=["core", "smoke", "custom"],
        help="Which test suite to run",
    )
    parser.add_argument("--gold", help="Path to custom gold JSON (when suite=custom)")
    parser.add_argument("--timeout", type=float, default=60.0, help="Per-request timeout (s)")
    args = parser.parse_args()

    if args.suite == "smoke":
        gold_path = SMOKE_GOLD
    elif args.suite == "core":
        gold_path = CORE_GOLD if CORE_GOLD.exists() else DEFAULT_GOLD
    else:
        if not args.gold:
            print("Custom suite requires --gold", file=sys.stderr)
            return
        gold_path = pathlib.Path(args.gold)

    data = json.loads(gold_path.read_text())
    cases = data.get("cases", [])
    if not cases:
        print(f"No cases in {gold_path.name}")
        return

    timestamp = time.strftime("%Y%m%d-%H%M%S")
    run_dir = BASE / f"run-{timestamp}"
    run_dir.mkdir(parents=True, exist_ok=True)
    meta = {
        "endpoint": args.endpoint,
        "suite": args.suite,
        "gold": str(gold_path),
        "env": {
            "LLM_MODEL": os.getenv("LLM_MODEL"),
            "OPENAI_BASE_URL": os.getenv("OPENAI_BASE_URL"),
            "GRAMMAR_ONLY": os.getenv("GRAMMAR_ONLY"),
            "TYPOGRAPHY_CHECK": os.getenv("TYPOGRAPHY_CHECK"),
            "LLM_TIMEOUT": os.getenv("LLM_TIMEOUT"),
        },
        "timestamp": timestamp,
    }
    (run_dir / "run_meta.json").write_text(json.dumps(meta, indent=2))

    total_expected = 0
    total_tp = 0
    total_fn = 0
    total_fp = 0
    total_wrong = 0
    total_tp_lenient = 0
    total_fn_lenient = 0
    total_fp_lenient = 0
    total_wrong_lenient = 0

    report_lines = []
    per_case_latency = []

    for case in cases:
        case_id = case.get("id", "case")
        text = case.get("text", "")
        language = case.get("language", "en-GB")
        expected = case.get("expected", [])

        status, body, latency_ms = post_check(text, language, timeout=args.timeout)
        per_case_latency.append(latency_ms)
        (run_dir / f"{case_id}_request.json").write_text(
            json.dumps({"text": text, "language": language}, indent=2)
        )
        (run_dir / f"{case_id}_response.json").write_text(body)

        case_tp = case_fn = case_fp = case_wrong = 0
        case_tp_lenient = case_fn_lenient = case_fp_lenient = case_wrong_lenient = 0
        matches = []
        by_error = {}
        missing_error_text = 0

        if status == 200:
            try:
                resp = json.loads(body)
                matches = resp.get("matches", []) if isinstance(resp, dict) else []
            except Exception as exc:
                report_lines.append(f"{case_id}: JSON parse error: {exc}")
                continue
        else:
            report_lines.append(f"{case_id}: HTTP {status}")
            continue

        for m in matches:
            err = m.get("error_text")
            if not err:
                off = m.get("offset")
                length = m.get("length")
                if isinstance(off, int) and isinstance(length, int):
                    err = text[off : off + length]
                else:
                    missing_error_text += 1
                    continue
            repls = normalise_replacements(m.get("replacements", []))
            by_error.setdefault(err, set()).update(repls)

        expected_by_error = {e.get("error_text"): e for e in expected}
        total_expected += len(expected)

        for err, entry in expected_by_error.items():
            accept = set(entry.get("accept", []))
            accept_contains = set(entry.get("accept_contains", []))
            matched_errors = [k for k in by_error.keys() if _matches_error_text(k, entry)]
            if not matched_errors:
                case_fn += 1
                case_fn_lenient += 1
                continue

            repls = set()
            for k in matched_errors:
                repls.update(by_error.get(k, set()))

            if accept.intersection(repls):
                case_tp += 1
            else:
                case_wrong += 1

            if accept.intersection(repls):
                case_tp_lenient += 1
            elif accept_contains and any(any(token in r for token in accept_contains) for r in repls):
                case_tp_lenient += 1
            else:
                case_wrong_lenient += 1

        for err in by_error:
            if not any(_matches_error_text(err, entry) for entry in expected):
                case_fp += 1
                case_fp_lenient += 1

        total_tp += case_tp
        total_fn += case_fn
        total_fp += case_fp
        total_wrong += case_wrong
        total_tp_lenient += case_tp_lenient
        total_fn_lenient += case_fn_lenient
        total_fp_lenient += case_fp_lenient
        total_wrong_lenient += case_wrong_lenient

        report_lines.append(
            f"{case_id}: strict TP={case_tp} FN={case_fn} FP={case_fp} wrong_repl={case_wrong} | "
            f"lenient TP={case_tp_lenient} FN={case_fn_lenient} FP={case_fp_lenient} wrong_repl={case_wrong_lenient} | "
            f"missing_error_text={missing_error_text}"
        )

    precision = (total_tp / (total_tp + total_fp)) if (total_tp + total_fp) else 0.0
    recall = (total_tp / (total_tp + total_fn)) if (total_tp + total_fn) else 0.0
    precision_lenient = (
        (total_tp_lenient / (total_tp_lenient + total_fp_lenient))
        if (total_tp_lenient + total_fp_lenient)
        else 0.0
    )
    recall_lenient = (
        (total_tp_lenient / (total_tp_lenient + total_fn_lenient))
        if (total_tp_lenient + total_fn_lenient)
        else 0.0
    )

    report_lines.append("")
    report_lines.append(f"Total expected: {total_expected}")
    report_lines.append(f"Total TP (strict): {total_tp}")
    report_lines.append(f"Total FN (strict): {total_fn}")
    report_lines.append(f"Total FP (strict): {total_fp}")
    report_lines.append(f"Total wrong_repl (strict): {total_wrong}")
    report_lines.append(f"Precision (strict): {precision:.2%}")
    report_lines.append(f"Recall (strict): {recall:.2%}")
    report_lines.append("")
    report_lines.append(f"Total TP (lenient): {total_tp_lenient}")
    report_lines.append(f"Total FN (lenient): {total_fn_lenient}")
    report_lines.append(f"Total FP (lenient): {total_fp_lenient}")
    report_lines.append(f"Total wrong_repl (lenient): {total_wrong_lenient}")
    report_lines.append(f"Precision (lenient): {precision_lenient:.2%}")
    report_lines.append(f"Recall (lenient): {recall_lenient:.2%}")
    if per_case_latency:
        report_lines.append(
            f"Latency per case (ms): avg={mean(per_case_latency):.2f}, max={max(per_case_latency):.2f}"
        )

    report = "\n".join(report_lines)
    (run_dir / "report.txt").write_text(report)
    print(report)


if __name__ == "__main__":
    main()
