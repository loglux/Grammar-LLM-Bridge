# qa-results/

QA tooling and curated test suites. Two subdirectories with different purposes:

## `quality/` — curated suites + prompt A/B runs

Tracked in git. Used to compare model behaviour against gold expectations and to study how prompt blocks influence results.

- `qa_gold.json`, `qa_sva.json`, `qa_punct_gold.json`, `gold_core.json`, `gold_smoke.json`, `gold_latex.json` — gold suites grouped by category.
- `run_quality.py`, `run_punct_quality.py`, `score_run.py`, `ab_chunk_test.py`, `diag_deepseek_chunks.py` — runners that hit the Bridge `/v2/check` endpoint and compare matches to the gold expectations.
- `prompt_compare_direct/`, `prompt_compare_selfcheck_*/`, `prompt_compare_task_selfcheck/` — A/B prompt experiments: each case is run with `_baseline` and a variant (e.g. `_punc_rule`), letting us see how flipping a single prompt block changes the model's output. Companion writeup: [`../../docs/sva_prompt_update.md`](../../docs/sva_prompt_update.md).

A typical session: pick a gold suite, run `run_quality.py` against a Bridge running the model you want to test, score with `score_run.py`, diff against the previous run.

## `ad-hoc/` — sample inputs + ad-hoc tools

Tracked in git (the tools and sample texts). Run outputs (`run-*`, `latency-run-*`, etc.) are gitignored and only live locally — see [`../.gitignore`](../.gitignore) for the exact patterns.

- `samples/` — short test inputs with intentional errors (`hard*.txt`, `sample*.txt`, `press*.txt`).
- `seed_tests/`, `max_tokens_samples/` — additional sample groupings.
- `run_samples.py` — iterates over `samples/*.txt`, hits `/v2/check`, writes per-sample output dirs and a report.
- `analyze_last_run.py` — picks the newest `run-*` dir and writes a `report.txt` with sanity checks (duplicate spans, empty replacements, missing fields).
- `run_marker_suite.py`, `run_sva_prompt_ab.py`, `test_prompt_markers.py`, `test_single_prompt.py` — focused exploratory runners for prompt experiments.
- `latency_*.py` — latency benchmarking helpers.

The `Makefile` exposes a couple of convenience targets:

```bash
make smoke   # runs run_samples.py against the dev endpoint (:9019)
make report  # runs analyze_last_run.py over the latest run-* dir
```
