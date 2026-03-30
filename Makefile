.PHONY: infra infra-down infra-logs infra-reset dev web api migrate downgrade migration seed lint format typecheck test test-api test-web test-watch check clean help

WEB_DIR := apps/web
API_DIR := apps/api

##@ Infrastructure
infra: ## Start Postgres, Redis, RabbitMQ
	docker compose up -d

infra-down: ## Stop infrastructure
	docker compose down

infra-logs: ## Tail infrastructure logs
	docker compose logs -f

infra-reset: ## Stop infrastructure and destroy volumes
	docker compose down -v

##@ Development
dev: infra ## Start web + api concurrently (requires make -j2)
	$(MAKE) -j2 web api

web: ## Start Next.js dev server
	cd $(WEB_DIR) && bun dev

api: ## Start FastAPI dev server
	cd $(API_DIR) && poetry run uvicorn main:app --reload --port 8000

##@ Database
migrate: ## Run alembic migrations
	cd $(API_DIR) && poetry run alembic upgrade head

downgrade: ## Rollback one alembic migration
	cd $(API_DIR) && poetry run alembic downgrade -1

migration: ## Create a new alembic migration (prompts for name)
	@read -p "Migration name: " name; \
	cd $(API_DIR) && poetry run alembic revision --autogenerate -m "$$name"

seed: ## Seed ledger accounts
	cd $(API_DIR) && poetry run python -m scripts.seed

##@ Quality
lint: ## Fix lint + format issues (api + web)
	cd $(API_DIR) && poetry run ruff check --fix . && poetry run black . && poetry run isort .
	cd $(WEB_DIR) && bun run lint && bun run format

format: lint ## Alias for lint

typecheck: ## Run type checkers (mypy + tsc)
	cd $(API_DIR) && poetry run mypy .
	cd $(WEB_DIR) && bun tsc --noEmit

##@ Testing
test: test-api test-web ## Run all tests

test-api: ## Run pytest
	cd $(API_DIR) && poetry run pytest

test-web: ## Run web tests
	cd $(WEB_DIR) && bun run test

test-watch: ## Run web tests in watch mode
	cd $(WEB_DIR) && bun run test --watch

##@ CI
check: ## Read-only lint check + all tests
	cd $(API_DIR) && poetry run ruff check . && poetry run black --check . && poetry run isort --check-only .
	cd $(WEB_DIR) && bun run lint
	cd $(API_DIR) && poetry run mypy .
	cd $(WEB_DIR) && bun tsc --noEmit
	$(MAKE) test

##@ Cleanup
clean: ## Remove caches and compiled files
	find $(API_DIR) -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find $(API_DIR) -type d -name .mypy_cache -exec rm -rf {} + 2>/dev/null || true
	find $(API_DIR) -type d -name .ruff_cache -exec rm -rf {} + 2>/dev/null || true
	find $(API_DIR) -name "*.pyc" -delete 2>/dev/null || true

##@ Help
help: ## Show this help
	@awk 'BEGIN {FS = ":.*##"; printf "\nUsage:\n  make \033[36m<target>\033[0m\n"} /^##@/ { printf "\n\033[1m%s\033[0m\n", substr($$0, 5) } /^[a-zA-Z_-]+:.*##/ { printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2 }' $(MAKEFILE_LIST)

.DEFAULT_GOAL := help
