# Campus Locker System - Docker Deployment Makefile

.PHONY: help build up down logs test clean safe-test quick-test

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
	@echo "Service URLs (when running):"
	@echo "  📱 Main App: http://localhost"
	@echo "  📧 MailHog: http://localhost:8025"
	@echo "  🏥 Health: http://localhost/health"

# Production deployment
build:
	@echo "🔨 Building Docker images..."
	@echo "🔑 Generating new SECRET_KEY for security..."
	@echo "SECRET_KEY=$$(openssl rand -hex 32)" > .env
	docker-compose build

up:
	@echo "🚀 Starting production deployment..."
	@echo "🔑 Generating new SECRET_KEY for security..."
	@echo "SECRET_KEY=$$(openssl rand -hex 32)" > .env
	docker-compose up -d
	@echo "✅ Services started! Run 'make test' to verify deployment."

down:
	@echo "🛑 Stopping production deployment..."
	@echo "🔐 Logging out any active admin sessions..."
	@curl -s -X POST http://localhost/system/logout-all-admins > /dev/null 2>&1 || echo "ℹ️  No active sessions to logout (service may already be down)"
	docker-compose down

logs:
	@echo "📋 Viewing production logs..."
	docker-compose logs -f

# Testing deployment
test:
	@echo "🧪 Testing deployment..."
	@if [ -f scripts/test-deployment.sh ]; then \
		./scripts/test-deployment.sh; \
	else \
		echo "❌ Test script not found. Running basic health check..."; \
		echo "🔗 Service URLs:"; \
		echo "  📱 Main App: http://localhost"; \
		echo "  📧 MailHog: http://localhost:8025"; \
		echo "  🏥 Health: http://localhost/health"; \
		curl -f http://localhost/health || echo "❌ Health check failed"; \
	fi

# Safe testing (doesn't delete databases)
safe-test:
	@echo "🧪 Running safe tests (databases preserved)..."
	@echo "✅ Running basic health check..."
	@curl -s -f http://localhost/health > /dev/null && echo "✅ Application is healthy" || echo "❌ Health check failed"
	@echo "✅ Running application tests..."
	@curl -s -o /dev/null -w "%{http_code}" http://localhost/ | grep -q "200" && echo "✅ Main page loads" || echo "❌ Main page failed"
	@echo "✅ Running email service check..."
	@curl -s -f http://localhost:8025 > /dev/null && echo "✅ MailHog is accessible" || echo "❌ MailHog failed"

# Cleanup Docker resources
clean:
	@echo "🧹 Cleaning up Docker resources..."
	@echo "🔐 Logging out any active admin sessions..."
	@curl -s -X POST http://localhost/system/logout-all-admins > /dev/null 2>&1 || echo "ℹ️  No active sessions to logout (service may already be down)"
	docker-compose down -v
	docker system prune -f
	@echo "🔑 Removing security keys..."
	@rm -f .env
	@echo "✅ Cleanup complete!"

# Quick deployment test
quick-test:
	@echo "⚡ Quick deployment test..."
	@curl -s -f http://localhost/health > /dev/null && echo "✅ Application is healthy" || echo "❌ Application is not responding"
	@curl -s -f http://localhost:8025 > /dev/null && echo "✅ MailHog is accessible" || echo "❌ MailHog is not responding" 