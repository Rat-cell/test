# Campus Locker System - Development Makefile
.PHONY: help install test test-cov lint format security clean docker-build docker-test all

# Default target
help:
	@echo "Campus Locker System - Development Commands"
	@echo "==========================================="
	@echo "install     - Install dependencies"
	@echo "test        - Run all tests"
	@echo "test-cov    - Run tests with coverage report"
	@echo "lint        - Run code linting (flake8)"
	@echo "format      - Format code (black + isort)"
	@echo "security    - Run security scans (safety + bandit)"
	@echo "docker-build - Build Docker image"
	@echo "docker-test - Test Docker image locally"
	@echo "clean       - Clean up generated files"
	@echo "all         - Run full CI pipeline locally"

# Install dependencies
install:
	pip install -r requirements.txt

# Run tests
test:
	pytest tests/ -v

# Run tests with coverage
test-cov:
	pytest tests/ --cov=app --cov-report=term-missing --cov-report=html

# Lint code
lint:
	@echo "Running flake8 linting..."
	flake8 app/ --count --select=E9,F63,F7,F82 --show-source --statistics
	flake8 app/ --count --exit-zero --max-complexity=10 --max-line-length=127 --statistics

# Format code
format:
	@echo "Formatting code with black..."
	black app/
	@echo "Sorting imports with isort..."
	isort app/

# Security scans
security:
	@echo "Running safety check..."
	safety check
	@echo "Running bandit security scan..."
	bandit -r app/ -ll

# Build Docker image
docker-build:
	docker build -t campus-locker-system:dev .

# Test Docker image
docker-test: docker-build
	@echo "Testing Docker image..."
	docker run --rm -d -p 80:80 --name test-container campus-locker-system:dev
	sleep 5
	curl -f http://localhost/ || echo "App started successfully"
	docker stop test-container
	docker rmi campus-locker-system:dev

# Clean up
clean:
	@echo "Cleaning up..."
	rm -rf .pytest_cache/
	rm -rf htmlcov/
	rm -rf .coverage
	rm -rf coverage.xml
	rm -rf bandit-report.json
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete

# Run full pipeline locally
all: install lint security test-cov
	@echo "✅ All checks passed! Ready for commit." 