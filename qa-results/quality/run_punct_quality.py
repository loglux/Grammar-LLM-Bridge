"""
Run punctuation/boundary gold-set quality checks.
Writes per-case responses and a summary report.

Requirements: python3 (stdlib only). Endpoint: http://localhost:9019/v2/check
"""

import json
import pathlib
import time
import urllib.request

BASE = pathlib.Path(__file__).resolve().parent
GOLD_PATH = BASE / "qa_punct_gold.json"
ENDPOINT = "http://localhost:9019/v2/check"


def post_check(text: str, language: str) -> tuple[int, str]:
    payload = json.dumps({"text": text, "language": language}).encode("utf-8")
    req = urllib.request.Request(
        ENDPOINT,
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        status = resp.status
        body = resp.read().decode("utf-8")
    return status, body


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
    data = json.loads(GOLD_PATH.read_text())
    cases = data.get("cases", [])
    if not cases:
        print("No cases in qa_punct_gold.json")
        return

    timestamp = time.strftime("%Y%m%d-%H%M%S")
    run_dir = BASE / f"punct-run-{timestamp}"
    run_dir.mkdir(parents=True, exist_ok=True)

    total_expected = 0
    total_tp = 0
    total_fn = 0
    total_fp = 0
    total_wrong = 0

    report_lines = []

    for case in cases:
        case_id = case.get("id", "case")
        text = case.get("text", "")
        language = case.get("language", "en-GB")
        expected = case.get("expected", [])

        status, body = post_check(text, language)
        (run_dir / f"{case_id}_request.json").write_text(
            json.dumps({"text": text, "language": language}, indent=2)
        )
        (run_dir / f"{case_id}_response.json").write_text(body)

        case_tp = case_fn = case_fp = case_wrong = 0
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

        total_expected += len(expected)

        for entry in expected:
            accept = set(entry.get("accept", []))
            matched_errors = [k for k in by_error.keys() if _matches_error_text(k, entry)]
            if not matched_errors:
                case_fn += 1
                continue

            repls = set()
            for k in matched_errors:
                repls.update(by_error.get(k, set()))

            if accept.intersection(repls):
                case_tp += 1
            else:
                case_wrong += 1

        for err in by_error:
            if not any(_matches_error_text(err, entry) for entry in expected):
                case_fp += 1

        total_tp += case_tp
        total_fn += case_fn
        total_fp += case_fp
        total_wrong += case_wrong

        report_lines.append(
            f"{case_id}: TP={case_tp} FN={case_fn} FP={case_fp} wrong_repl={case_wrong} missing_error_text={missing_error_text}"
        )

    precision = (total_tp / (total_tp + total_fp)) if (total_tp + total_fp) else 0.0
    recall = (total_tp / (total_tp + total_fn)) if (total_tp + total_fn) else 0.0

    report_lines.append("")
    report_lines.append(f"Total expected: {total_expected}")
    report_lines.append(f"Total TP: {total_tp}")
    report_lines.append(f"Total FN: {total_fn}")
    report_lines.append(f"Total FP: {total_fp}")
    report_lines.append(f"Total wrong_repl: {total_wrong}")
    report_lines.append(f"Precision: {precision:.2%}")
    report_lines.append(f"Recall: {recall:.2%}")

    report = "\n".join(report_lines)
    (run_dir / "report.txt").write_text(report)
    print(report)


if __name__ == "__main__":
    main()
