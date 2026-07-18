# ai-employee Makefile

.PHONY: help install dev build test lint typecheck clean serve-api serve-web serve-all

help:  ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

install:  ## Install dependencies
	uv sync --all-extras
	cd web && npm install

dev:  ## Run dev server (api + web)
	@echo "Run in separate terminals:"
	@echo "  make serve-api"
	@echo "  make serve-web"

serve-api:  ## Run API server
	uv run python -m api.main --reload

serve-web:  ## Run web dev server
	cd web && npm run dev

serve-all:  ## Run all (api + web + ollama)
	@echo "Starting all services..."
	@trap 'kill 0' SIGINT; \
	uv run python -m api.main & \
	cd web && npm run dev & \
	ollama serve & \
	wait

build:  ## Build for production
	uv build
	cd web && npm run build

test:  ## Run tests
	uv run pytest tests/unit -v

test-all:  ## Run all tests including integration
	uv run pytest -v --cov

lint:  ## Lint code
	uv run ruff check .
	cd web && npm run lint

typecheck:  ## Type check
	uv run mypy core/ api/ eval/
	cd web && npm run typecheck

eval:  ## Run eval suite
	uv run python -m eval.runner

docker-build:  ## Build Docker images
	docker compose -f infra/docker-compose.yaml build

docker-up:  ## Start Docker stack
	docker compose -f infra/docker-compose.yaml up -d

docker-down:  ## Stop Docker stack
	docker compose -f infra/docker-compose.yaml down

clean:  ## Clean build artifacts
	rm -rf .pytest_cache .mypy_cache .ruff_cache dist build
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	rm -rf web/.next web/node_modules
