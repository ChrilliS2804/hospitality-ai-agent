.PHONY: help setup test test-unit test-integration lint format coverage \
        tf-init tf-plan tf-apply tf-destroy \
        deploy-functions deploy-layers build-layer \
        local-infra clean

# Default environment
env ?= dev

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-25s\033[0m %s\n", $$1, $$2}'

# ── Python ────────────────────────────────────────────────────────────────────

setup: ## Create venv and install all dev dependencies
	python -m venv .venv
	.venv/Scripts/pip install --upgrade pip
	.venv/Scripts/pip install -r requirements-dev.txt
	.venv/Scripts/pip install -e services/shared
	.venv/Scripts/pip install -e services/call-handler
	.venv/Scripts/pre-commit install --install-hooks

test: ## Run all tests
	pytest

test-unit: ## Run unit tests only
	pytest -m unit

test-integration: ## Run integration tests only (uses moto)
	pytest -m integration

coverage: ## Run tests with coverage report
	pytest --cov=services --cov-report=html --cov-report=term-missing

lint: ## Run ruff linter
	ruff check services tests

format: ## Auto-format with ruff
	ruff format services tests

typecheck: ## Run mypy type checking
	mypy services

# ── Terraform ─────────────────────────────────────────────────────────────────

tf-init: ## Initialise Terraform for an environment (env=dev|test|prod)
	terraform -chdir=terraform/environments/$(env) init -backend-config=backend.tfvars

tf-plan: ## Plan Terraform changes (env=dev|test|prod)
	terraform -chdir=terraform/environments/$(env) plan -var-file=terraform.tfvars

tf-apply: ## Apply Terraform changes (env=dev|test|prod)
	terraform -chdir=terraform/environments/$(env) apply -var-file=terraform.tfvars

tf-destroy: ## Destroy Terraform resources (env=dev|test|prod)
	@echo "WARNING: This will destroy all resources in $(env)"
	terraform -chdir=terraform/environments/$(env) destroy -var-file=terraform.tfvars

tf-fmt: ## Format all Terraform files
	terraform fmt -recursive terraform/

tf-validate: ## Validate all Terraform files
	terraform -chdir=terraform/environments/$(env) validate

# ── Lambda ────────────────────────────────────────────────────────────────────

build-layer: ## Build the shared Lambda layer zip
	mkdir -p build/layer/python
	pip install -r services/shared/requirements.txt -t build/layer/python
	cd build/layer && zip -r ../../build/shared-layer.zip python/

deploy-functions: ## Deploy all Lambda function packages (env=dev|test|prod)
	@for service in call-handler reservation-service faq-service notification-service handoff-service; do \
		echo "Packaging $$service..."; \
		cd services/$$service && zip -r ../../build/$$service.zip . -x "tests/*" "*.pyc" "__pycache__/*"; \
		cd ../..; \
	done
	@echo "Uploading to S3..."
	aws s3 sync build/ s3://$(env)-hospitality-lambda-packages/ --exclude "*" --include "*.zip"

# ── Local Dev ─────────────────────────────────────────────────────────────────

local-infra: ## Start local AWS services via moto server (for integration tests)
	@echo "Using moto for local AWS mocking — no server needed."
	@echo "Set AWS_DEFAULT_REGION=eu-central-1 and run pytest -m integration"

clean: ## Remove build artifacts
	rm -rf build/ .pytest_cache/ htmlcov/ .coverage
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
