"""
Quick helper to inspect the latest ad-hoc run under qa-results/ad-hoc/run-*/.
- Finds the most recent run directory.
- Loads response.json and request.json if present.
- Reports counts and anomalies:
  * JSON parse issues
  * Missing replacements
  * Duplicate spans (offset, length)
- Writes a brief report to <run>/report.txt and prints it.

This is a local QA helper; not part of the main app.
"""

import json
import pathlib
from typing import List, Dict, Tuple


BASE = pathlib.Path(__file__).resolve().parent


def find_latest_run() -> pathlib.Path:
    runs = sorted([p for p in BASE.iterdir() if p.is_dir() and p.name.startswith("run-")])
    if not runs:
        raise SystemExit("No run-* directories found.")
    return runs[-1]


def load_json(path: pathlib.Path):
    try:
        return json.loads(path.read_text()), None
    except Exception as e:
        return None, f"{path.name}: {e}"


def analyze_response(data: Dict) -> Tuple[List[str], List[str]]:
    issues = []
    summary = []

    matches = data.get("matches", []) if isinstance(data, dict) else []
    summary.append(f"Total matches: {len(matches)}")

    # Message/explanation presence
    missing_msg = [i for i, m in enumerate(matches) if not (m.get("message") or m.get("explanation"))]
    if missing_msg:
        summary.append(f"Missing message/explanation: {len(missing_msg)} at {missing_msg}")

    # Check duplicates by (offset, length)
    by_span: Dict[Tuple[int, int], List[Dict]] = {}
    for m in matches:
        off = m.get("offset")
        length = m.get("length")
        key = (off, length)
        by_span.setdefault(key, []).append(m)

    dup_spans = [(k, v) for k, v in by_span.items() if len(v) > 1]
    summary.append(f"Duplicate spans: {len(dup_spans)}")
    for key, group in dup_spans:
        msgs = [g.get("message") for g in group]
        summary.append(f"  span {key}: {msgs}")

    # Empty/absent replacements
    for idx, m in enumerate(matches):
        repls_raw = m.get("replacements", [])
        repls = []
        for r in repls_raw:
            if isinstance(r, dict):
                repls.append(r.get("value"))
            elif isinstance(r, str):
                repls.append(r)
            else:
                repls.append(None)
        if not repls or all(not r for r in repls):
            err = m.get("error_text") or (m.get("context") or {}).get("text")
            msg = m.get("message")
            issues.append(f"Match {idx}: empty replacements for '{err}' msg '{msg}'")

    return summary, issues


def main():
    run_dir = find_latest_run()
    report_lines = [f"Run directory: {run_dir.name}"]

    resp_path = run_dir / "response.json"
    req_path = run_dir / "request.json"

    resp, err = load_json(resp_path)
    if err:
        report_lines.append(f"Response JSON error: {err}")
    if req_path.exists():
        req, req_err = load_json(req_path)
        if req_err:
            report_lines.append(f"Request JSON error: {req_err}")
        else:
            report_lines.append(f"Request length: {len(req.get('text', ''))} chars")

    if resp and not err:
        summary, issues = analyze_response(resp)
        report_lines.extend(summary)
        if issues:
            report_lines.append("Issues:")
            report_lines.extend(f"- {line}" for line in issues)
        else:
            report_lines.append("Issues: none")

    report = "\n".join(report_lines)
    print(report)
    (run_dir / "report.txt").write_text(report)


if __name__ == "__main__":
    main()
