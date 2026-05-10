#!/usr/bin/env bash
set -euo pipefail

# Redeploys the grammar-llm stack with the DNS/extra_hosts workaround.
# Usage: ./compose-deploy.sh [--with-dev]

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

WITH_DEV=0
if [[ "${1-}" == "--with-dev" ]]; then
  WITH_DEV=1
  shift
fi

if [[ "$#" -ne 0 ]]; then
  echo "Usage: $0 [--with-dev]" >&2
  exit 1
fi

echo "[grammar-llm] Stopping existing stack..."
docker compose down
docker compose --profile dev down

if docker network inspect grammar-llm-net >/dev/null 2>&1; then
  echo "[grammar-llm] Removing stale network grammar-llm-net..."
  docker network rm grammar-llm-net
fi

if [[ $WITH_DEV -eq 1 ]]; then
  echo "[grammar-llm] Starting stack (prod + dev profile)..."
  docker compose --profile dev up -d
else
  echo "[grammar-llm] Starting stack (prod only)..."
  docker compose up -d
fi

echo "[grammar-llm] Active containers:"
docker compose ps
