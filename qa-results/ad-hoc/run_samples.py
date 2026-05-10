"""
Run all sample texts in qa-results/ad-hoc/samples/ against the local Grammar-LLM-Bridge.
Creates a run directory per sample, saves request/response, and writes a brief report.

Requirements: python3 (stdlib only). Endpoint: http://localhost:9019/v2/check
"""

import json
import pathlib
import time
import urllib.request

BASE = pathlib.Path(__file__).resolve().parent
SAMPLES_DIR = BASE / "samples"


def post_check(text: str, language: str = "en-GB") -> tuple[int, str]:
    payload = json.dumps({"text": text, "language": language}).encode("utf-8")
    req = urllib.request.Request(
        "http://localhost:9019/v2/check",
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        status = resp.status
        body = resp.read().decode("utf-8")
    return status, body


def analyze_response(data: dict, original_text: str) -> list[str]:
    issues: list[str] = []
    matches = data.get("matches", []) if isinstance(data, dict) else []

    # Duplicate spans
    by_span = {}
    for m in matches:
        key = (m.get("offset"), m.get("length"))
        by_span.setdefault(key, []).append(m)
    for key, group in by_span.items():
        if len(group) > 1:
            msgs = [g.get("message") for g in group]
            issues.append(f"Duplicate span {key}: {msgs}")

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
            issues.append(f"Match {idx}: empty replacements for '{err}'")

    # Missing message/explanation
    missing_msg = [i for i, m in enumerate(matches) if not (m.get("message") or m.get("explanation"))]
    if missing_msg:
        issues.append(f"Missing message/explanation at indices: {missing_msg}")

    # Missing error_text (LT-format responses omit it; not fatal, but log indices)
    missing_error = [i for i, m in enumerate(matches) if not m.get("error_text")]
    if missing_error:
        issues.append(f"Missing error_text at indices (likely LT-format): {missing_error}")
        for i in missing_error:
            m = matches[i]
            off, length = m.get("offset"), m.get("length")
            snippet = ""
            if isinstance(off, int) and isinstance(length, int):
                snippet = original_text[off : off + length]
            issues.append(f"  idx {i} span ({off},{length}) -> '{snippet}'")

    return issues


def main():
    timestamp = time.strftime("%Y%m%d-%H%M%S")
    samples = sorted(SAMPLES_DIR.glob("sample*.txt"))
    if not samples:
        print("No samples found.")
        return

    for sample in samples:
        text = sample.read_text()
        run_dir = BASE / f"run-{timestamp}-{sample.stem}"
        run_dir.mkdir(parents=True, exist_ok=True)

        # Save request
        req_path = run_dir / "request.json"
        request_obj = {"text": text, "language": "en-GB"}
        req_path.write_text(json.dumps(request_obj, indent=2))

        # Call API
        status, body = post_check(text)
        resp_path = run_dir / "response.json"
        resp_path.write_text(body)

        report_lines = [f"Sample: {sample.name}", f"HTTP status: {status}"]
        issues: list[str] = []

        if status == 200:
            try:
                data = json.loads(body)
                issues = analyze_response(data, text)
                report_lines.append(f"Matches: {len(data.get('matches', [])) if isinstance(data, dict) else 'n/a'}")
            except Exception as e:
                issues.append(f"JSON parse error: {e}")
        else:
            issues.append(f"Non-200 response: {body[:200]}")

        if issues:
            report_lines.append("Issues:")
            report_lines.extend(f"- {i}" for i in issues)
        else:
            report_lines.append("Issues: none")

        report = "\n".join(report_lines)
        (run_dir / "report.txt").write_text(report)
        print(report)


if __name__ == "__main__":
    main()
