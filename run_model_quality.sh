#!/usr/bin/env bash
# Usage: ./run_model_quality.sh <model> [port] [base_url] [api_key]
# Runs a one-off quality suite against a temporary container and cleans up.

set -euo pipefail

MODEL="${1:-}"
PORT="${2:-9040}"
BASE_URL="${3:-https://api.openai.com/v1}"
API_KEY="${4:-${OPENAI_API_KEY:-}}"
SUITE="${5:-core}"
GOLD_PATH="${6:-}"

if [[ -z "$MODEL" || -z "$API_KEY" ]]; then
  echo "Usage: $0 <model> [port] [base_url] [api_key] [suite] [gold_path]" >&2
  exit 1
fi

NAME="qa-test-$$"
echo "Starting container $NAME on port $PORT for model: $MODEL"
docker run -d --name "$NAME" -p "$PORT:8000" \
  -e OPENAI_API_KEY="$API_KEY" \
  -e OPENAI_BASE_URL="$BASE_URL" \
  -e LLM_MODEL="$MODEL" \
  -e GRAMMAR_ONLY=true \
  -e TYPOGRAPHY_CHECK=false \
  -e LLM_TIMEOUT=120 \
  grammar-llm-bridge:latest \
  uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 2

sleep 5

cleanup() {
  echo "Stopping $NAME"
  docker rm -f "$NAME" >/dev/null 2>&1 || true
}
trap cleanup EXIT

echo "Running qa_results/quality/run_quality.py against http://localhost:$PORT/v2/check (suite=$SUITE${GOLD_PATH:+ gold=$GOLD_PATH})"
cd "$(dirname "$0")/qa-results/quality"

python3 - <<PY
import sys
import run_quality

run_quality.ENDPOINT = "http://localhost:${PORT}/v2/check"

argv = ["run_quality.py", "--suite", "${SUITE}"]
gold = "${GOLD_PATH}"
if gold:
    argv += ["--gold", gold]

sys.argv = argv
run_quality.main()
PY

echo "Done. Results in $(pwd)/run-$(ls -t run-* | head -n1)"
