"""
Score a saved run directory against qa_gold.json.
Defaults to the latest run-* directory (optionally filtered by suffix).
"""

import json
import pathlib
import sys

BASE = pathlib.Path(__file__).resolve().parent
GOLD_PATH = BASE / "qa_gold.json"


def normalise_replacements(repls_raw):
    repls = []
    for r in repls_raw or []:
        if isinstance(r, dict):
            repls.append(r.get("value"))
        elif isinstance(r, str):
            repls.append(r)
        else:
            repls.append(None)
    return [r for r in repls if r]


def matches_error_text(candidate, expected):
    if candidate == expected.get("error_text"):
        return True
    alts = expected.get("error_text_alt") or []
    return candidate in alts


def pick_run_dir(suffix=None):
    pattern = "run-*" if not suffix else f"run-*-{suffix}"
    runs = sorted(BASE.glob(pattern))
    if not runs:
        return None
    return runs[-1]


def main():
    suffix = None
    if len(sys.argv) > 1:
        suffix = sys.argv[1]

    run_dir = pick_run_dir(suffix=suffix)
    if not run_dir:
        print("No run directory found.")
        return

    gold = json.loads(GOLD_PATH.read_text())
    cases = gold.get("cases", [])

    total_expected = 0
    total_tp = total_fn = total_fp = total_wrong = 0
    total_tp_lenient = total_fn_lenient = total_fp_lenient = total_wrong_lenient = 0

    report_lines = [f"Run directory: {run_dir}"]

    for case in cases:
        case_id = case.get("id", "case")
        text = case.get("text", "")
        expected = case.get("expected", [])

        resp_path = run_dir / f"{case_id}_response.json"
        if not resp_path.exists():
            report_lines.append(f"{case_id}: missing response")
            continue

        resp = json.loads(resp_path.read_text())
        matches = resp.get("matches", []) if isinstance(resp, dict) else []

        by_error = {}
        missing_error_text = 0

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

        case_tp = case_fn = case_fp = case_wrong = 0
        case_tp_lenient = case_fn_lenient = case_fp_lenient = case_wrong_lenient = 0

        for entry in expected:
            accept = set(entry.get("accept", []))
            accept_contains = set(entry.get("accept_contains", []))
            matched_errors = [k for k in by_error if matches_error_text(k, entry)]
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
            if not any(matches_error_text(err, entry) for entry in expected):
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

    report = "\n".join(report_lines)
    (run_dir / "score.txt").write_text(report)
    print(report)


if __name__ == "__main__":
    main()
