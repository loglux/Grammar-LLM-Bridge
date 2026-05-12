# Grammar-LLM-Bridge — repo helper
# Run from the repo root.
# `make help` lists available targets.

VENV    := venv
PY      := $(VENV)/bin/python3
IMAGE   := grammar-llm-bridge:latest
COMPOSE := docker compose -f deploy/load-balancer/docker-compose.yml

MAKEFLAGS += --no-print-directory
.DEFAULT_GOAL := help

.PHONY: help build up up-dev down restart status \
        logs-01 logs-02 logs-lb logs-dev \
        smoke report quality quality-ru clean-pyc

help: ## Show this help
	@grep -hE '^[a-zA-Z0-9_-]+:.*?##' $(MAKEFILE_LIST) | sort | \
	  awk 'BEGIN {FS = ":.*?##"}; {printf "  \033[36m%-12s\033[0m %s\n", $$1, $$2}'

# --- Container ---

build: ## Build $(IMAGE) from Dockerfile
	docker build -t $(IMAGE) .

up: ## Start prod stack (LB :8081, two app replicas)
	$(COMPOSE) up -d

up-dev: ## Start dev profile (single instance on :9019)
	$(COMPOSE) --profile dev up -d

down: ## Stop and remove all stack containers (incl. dev)
	$(COMPOSE) --profile dev down

restart: ## Recreate prod containers from current image
	$(COMPOSE) up -d --force-recreate \
	  grammar-llm-01 grammar-llm-02 grammar-llm-balancer

status: ## Show running grammar-llm-* containers
	@docker ps -a --filter "name=grammar-llm" \
	  --format "table {{.Names}}\t{{.Status}}\t{{.Image}}"

# --- Logs (Ctrl-C to stop) ---

logs-01:  ## Tail grammar-llm-01
	docker logs -f grammar-llm-01
logs-02:  ## Tail grammar-llm-02
	docker logs -f grammar-llm-02
logs-lb:  ## Tail nginx balancer
	docker logs -f grammar-llm-balancer
logs-dev: ## Tail dev container
	docker logs -f grammar-llm-dev

# --- QA ---

smoke: ## Run sample batch (expects dev container on :9019)
	$(PY) qa-results/ad-hoc/run_samples.py

report: ## Analyse latest run-* under qa-results/ad-hoc
	$(PY) qa-results/ad-hoc/analyze_last_run.py

quality: ## Quality suite. Usage: make quality MODEL=deepseek-chat
	@test -n "$(MODEL)" || { \
	  echo "Set MODEL=… (e.g. make quality MODEL=deepseek-chat)" >&2; exit 1; }
	bash run_model_quality.sh $(MODEL)

quality-ru: ## Russian quality suite. Usage: make quality-ru MODEL=deepseek-chat [BASE_URL=…] [API_KEY=…]
	@test -n "$(MODEL)" || { \
	  echo "Set MODEL=… (e.g. make quality-ru MODEL=deepseek-chat)" >&2; exit 1; }
	bash run_model_quality.sh "$(MODEL)" 9040 \
	  "$(or $(BASE_URL),https://api.openai.com/v1)" \
	  "$(or $(API_KEY),$(OPENAI_API_KEY))" \
	  custom qa-results/quality/gold_ru.json

# --- House-keeping ---

clean-pyc: ## Remove __pycache__ trees (skips venv)
	@find . -path ./venv -prune -o -name __pycache__ -print -exec rm -rf {} + 2>/dev/null || true
