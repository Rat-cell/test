# Campus Locker System - Docker Deployment Makefile

.PHONY: help build up down logs test clean dev-up dev-down dev-logs

# Default target
help:
	@echo "🚀 Campus Locker System - Docker Deployment"
	@echo "============================================="
	@echo ""
	@echo "Available commands:"
	@echo "  make build      - Build Docker images"
	@echo "  make up         - Start production deployment"
	@echo "  make down       - Stop production deployment"
	@echo "  make logs       - View production logs"
	@echo "  make test       - Test deployment"
	@echo "  make clean      - Clean up Docker resources"
	@echo ""
	@echo "Development commands:"
	@echo "  make dev-up     - Start development deployment"
	@echo "  make dev-down   - Stop development deployment"
	@echo "  make dev-logs   - View development logs"
	@echo ""
	@echo "Service URLs (when running):"
	@echo "  📱 Main App: http://localhost"
	@echo "  📧 MailHog: http://localhost:8025"
	@echo "  🏥 Health: http://localhost/health"

# Production deployment
build:
	@echo "🔨 Building Docker images..."
	docker-compose build

up:
	@echo "🚀 Starting production deployment..."
	docker-compose up -d
	@echo "✅ Services started! Run 'make test' to verify deployment."

down:
	@echo "🛑 Stopping production deployment..."
	docker-compose down

logs:
	@echo "📋 Viewing production logs..."
	docker-compose logs -f

# Development deployment
dev-up:
	@echo "🚀 Starting development deployment..."
	docker-compose -f docker-compose.dev.yml up -d
	@echo "✅ Development services started!"

dev-down:
	@echo "🛑 Stopping development deployment..."
	docker-compose -f docker-compose.dev.yml down

dev-logs:
	@echo "📋 Viewing development logs..."
	docker-compose -f docker-compose.dev.yml logs -f

# Testing
test:
	@echo "🧪 Testing deployment..."
	@if [ -f scripts/test-deployment.sh ]; then \
		./scripts/test-deployment.sh; \
	else \
		echo "❌ Test script not found. Running basic health check..."; \
		curl -f http://localhost/health || echo "❌ Health check failed"; \
	fi

# Cleanup
clean:
	@echo "🧹 Cleaning up Docker resources..."
	docker-compose down -v
	docker-compose -f docker-compose.dev.yml down -v
	docker system prune -f
	@echo "✅ Cleanup complete!"

# Quick deployment test
quick-test:
	@echo "⚡ Quick deployment test..."
	@curl -s -f http://localhost/health > /dev/null && echo "✅ Application is healthy" || echo "❌ Application is not responding"
	@curl -s -f http://localhost:8025 > /dev/null && echo "✅ MailHog is accessible" || echo "❌ MailHog is not responding" 