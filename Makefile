# Makefile for WebArc project

.PHONY: help build lint typecheck test clean install docker-build docker-test docker-lint docker-typecheck docker-test-all

# Default target
help:
	@echo "WebArc Makefile"
	@echo ""
	@echo "Targets:"
	@echo "  build          - Build Docker image"
	@echo "  lint           - Run linting (ruff)"
	@echo "  typecheck      - Run type checking (mypy)"
	@echo "  test           - Run tests (pytest)"
	@echo "  clean          - Clean build artifacts"
	@echo "  install        - Install dependencies (in container)"
	@echo "  docker-build   - Build Docker image"
	@echo "  docker-lint    - Run linting in Docker"
	@echo "  docker-typecheck - Run type checking in Docker"
	@echo "  docker-test    - Run tests in Docker"
	@echo "  docker-test-all - Run all checks in Docker"

# Build Docker image
build: docker-build

docker-build:
	docker compose build 2>&1 | tee artifacts/docker-build.log

# Linting with ruff
lint:
	ruff check webarc/ tests/

docker-lint:
	docker compose run --rm --entrypoint="" webarc python -m ruff check webarc/ tests/ 2>&1 | tee artifacts/lint.log || true

# Type checking with mypy
typecheck:
	mypy webarc/ --ignore-missing-imports --no-strict-optional

docker-typecheck:
	docker compose run --rm --entrypoint="" webarc python -m mypy webarc/ --ignore-missing-imports --no-strict-optional 2>&1 | tee artifacts/typecheck.log || true

# Testing with pytest
test:
	pytest tests/ -v --cov=webarc --cov-report=html --cov-report=term

docker-test:
	docker compose run --rm --entrypoint="" webarc python -m pytest tests/ -v --cov=webarc --cov-report=html --cov-report=term --cov-report=json:artifacts/coverage.json 2>&1 | tee artifacts/test.log || true

# Run all checks in Docker
docker-test-all: docker-build docker-lint docker-typecheck docker-test

# Clean build artifacts
clean:
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info/
	rm -rf .pytest_cache/
	rm -rf .coverage
	rm -rf htmlcov/
	find . -type d -name __pycache__ -exec rm -r {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true

# Install dependencies (for local development)
install:
	pip install -r requirements.txt
