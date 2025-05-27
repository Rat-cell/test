#!/bin/bash

# Campus Locker System - Deployment Test Script
# This script tests the Docker deployment to ensure everything is working correctly

set -e  # Exit on any error

echo "🚀 Campus Locker System - Deployment Testing"
echo "=============================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
BASE_URL="http://localhost"
MAILHOG_URL="http://localhost:8025"
TIMEOUT=30

# Helper functions
log_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

log_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

log_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

log_error() {
    echo -e "${RED}❌ $1${NC}"
}

wait_for_service() {
    local url=$1
    local service_name=$2
    local max_attempts=30
    local attempt=1

    log_info "Waiting for $service_name to be ready..."
    
    while [ $attempt -le $max_attempts ]; do
        if curl -s -f "$url" > /dev/null 2>&1; then
            log_success "$service_name is ready!"
            return 0
        fi
        
        echo -n "."
        sleep 2
        attempt=$((attempt + 1))
    done
    
    log_error "$service_name failed to start within $((max_attempts * 2)) seconds"
    return 1
}

test_health_endpoint() {
    log_info "Testing health endpoint..."
    
    response=$(curl -s -w "%{http_code}" "$BASE_URL/health")
    http_code="${response: -3}"
    body="${response%???}"
    
    if [ "$http_code" = "200" ]; then
        log_success "Health endpoint is working (HTTP $http_code)"
        echo "Response: $body"
    else
        log_error "Health endpoint failed (HTTP $http_code)"
        return 1
    fi
}

test_main_pages() {
    log_info "Testing main application pages..."
    
    # Test deposit page
    if curl -s -f "$BASE_URL/deposit" > /dev/null; then
        log_success "Deposit page is accessible"
    else
        log_error "Deposit page is not accessible"
        return 1
    fi
    
    # Test pickup page
    if curl -s -f "$BASE_URL/pickup" > /dev/null; then
        log_success "Pickup page is accessible"
    else
        log_error "Pickup page is not accessible"
        return 1
    fi
    
    # Test admin login page
    if curl -s -f "$BASE_URL/admin/login" > /dev/null; then
        log_success "Admin login page is accessible"
    else
        log_error "Admin login page is not accessible"
        return 1
    fi
}

test_mailhog() {
    log_info "Testing MailHog email service..."
    
    if curl -s -f "$MAILHOG_URL" > /dev/null; then
        log_success "MailHog web interface is accessible"
    else
        log_error "MailHog web interface is not accessible"
        return 1
    fi
}

test_api_endpoints() {
    log_info "Testing API endpoints..."
    
    # Test health endpoint via API
    response=$(curl -s -H "Accept: application/json" "$BASE_URL/health")
    if echo "$response" | grep -q "healthy"; then
        log_success "API health endpoint is working"
    else
        log_error "API health endpoint failed"
        return 1
    fi
}

test_database_connectivity() {
    log_info "Testing database connectivity through health endpoint..."
    
    response=$(curl -s "$BASE_URL/health")
    if echo "$response" | grep -q "healthy"; then
        log_success "Database connectivity is working"
    else
        log_error "Database connectivity failed"
        return 1
    fi
}

run_container_health_checks() {
    log_info "Checking container health status..."
    
    # Check if containers are running
    containers=("campus_locker_app" "campus_locker_mailhog" "campus_locker_nginx")
    
    for container in "${containers[@]}"; do
        if docker ps --format "table {{.Names}}" | grep -q "$container"; then
            health=$(docker inspect --format='{{.State.Health.Status}}' "$container" 2>/dev/null || echo "no-healthcheck")
            if [ "$health" = "healthy" ] || [ "$health" = "no-healthcheck" ]; then
                log_success "Container $container is running and healthy"
            else
                log_warning "Container $container is running but health status: $health"
            fi
        else
            log_error "Container $container is not running"
            return 1
        fi
    done
}

show_service_urls() {
    echo ""
    log_info "Service URLs:"
    echo "📱 Main Application: $BASE_URL"
    echo "📧 MailHog (Email Testing): $MAILHOG_URL"
    echo "🏥 Health Check: $BASE_URL/health"
    echo "👤 Admin Login: $BASE_URL/admin/login"
    echo ""
}

main() {
    echo ""
    log_info "Starting deployment tests..."
    echo ""
    
    # Wait for services to be ready
    wait_for_service "$BASE_URL/health" "Campus Locker Application" || exit 1
    wait_for_service "$MAILHOG_URL" "MailHog Email Service" || exit 1
    
    echo ""
    log_info "Running functionality tests..."
    echo ""
    
    # Run tests
    test_health_endpoint || exit 1
    test_main_pages || exit 1
    test_mailhog || exit 1
    test_api_endpoints || exit 1
    test_database_connectivity || exit 1
    run_container_health_checks || exit 1
    
    echo ""
    log_success "🎉 All deployment tests passed!"
    echo ""
    
    show_service_urls
    
    log_info "Deployment is ready for use!"
}

# Run main function
main "$@" 