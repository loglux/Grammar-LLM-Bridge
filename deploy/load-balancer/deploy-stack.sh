#!/bin/sh
# Manage Grammar-LLM stack with fixed-IP network and compose.
# Usage:
#   ./deploy-stack.sh up        # rebuild image, recreate network, start stack (prod + dev)
#   ./deploy-stack.sh down      # stop stack and remove network
#   ./deploy-stack.sh restart   # down + up
#   ./deploy-stack.sh logs      # follow balancer + workers logs

set -e
ROOT="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$(cd "$ROOT/../.." && pwd)"
NETWORK_NAME="grammar-fixed-net"

build_image() {
  echo ">>> Building grammar-llm-bridge:latest"
  docker build -t grammar-llm-bridge:latest "$PROJECT_ROOT"
}

down_stack() {
  echo ">>> Stopping compose stack"
  (cd "$ROOT" && docker compose --profile dev down || true)
  (cd "$ROOT" && docker compose down || true)
}

remove_network() {
  echo ">>> Removing network $NETWORK_NAME (if exists)"
  docker network rm "$NETWORK_NAME" >/dev/null 2>&1 || true
}

up_stack() {
  echo ">>> Creating network $NETWORK_NAME and starting stack"
  (cd "$ROOT" && docker compose up -d)
  (cd "$ROOT" && docker compose --profile dev up -d grammar-llm-dev)
}

show_logs() {
  docker logs -f grammar-llm-balancer grammar-llm-01 grammar-llm-02
}

case "$1" in
  up)
    build_image
    down_stack
    remove_network
    up_stack
    ;;
  down)
    down_stack
    remove_network
    ;;
  restart)
    down_stack
    remove_network
    build_image
    up_stack
    ;;
  logs)
    show_logs
    ;;
  *)
    echo "Usage: $0 {up|down|restart|logs}"
    exit 1
    ;;
esac
