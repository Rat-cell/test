#!/bin/bash

# Campus Locker System v2.0 - Setup Script
# This script initializes the project for new users

set -e  # Exit on any error

echo "🚀 Campus Locker System v2.0 - Setup Script"
echo "=============================================="

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed. Please install Docker Desktop first."
    echo "   macOS/Windows: https://docs.docker.com/desktop/"
    echo "   Linux: https://docs.docker.com/engine/install/"
    exit 1
fi

# Check if Docker Compose is available
if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
    echo "❌ Docker Compose is not available. Please ensure Docker Desktop is running."
    exit 1
fi

# Check if Make is installed
if ! command -v make &> /dev/null; then
    echo "⚠️  Make is not installed. You can still use docker-compose commands directly."
    MAKE_AVAILABLE=false
else
    MAKE_AVAILABLE=true
fi

echo "✅ Prerequisites check passed!"
echo ""

# Create necessary directories
echo "📁 Creating necessary directories..."
mkdir -p campus_locker_system/databases
mkdir -p campus_locker_system/logs
mkdir -p scripts

# Set proper permissions for directories
chmod 755 campus_locker_system/databases
chmod 755 campus_locker_system/logs

echo "✅ Directories created successfully!"
echo ""

# Create sample environment file if it doesn't exist
if [ ! -f .env ]; then
    echo "🔧 Creating environment configuration..."
    cat > .env << EOL
# Campus Locker System v2.0 - Environment Configuration
# Production Environment Settings

# Application
FLASK_ENV=production
SECRET_KEY=your-secret-key-change-in-production

# Database
DATABASE_URL=sqlite:///databases/campus_locker.db
AUDIT_DATABASE_URL=sqlite:///databases/campus_locker_audit.db

# Email (MailHog for testing)
MAIL_SERVER=mailhog
MAIL_PORT=1025
MAIL_USE_TLS=False
MAIL_USE_SSL=False
MAIL_USERNAME=
MAIL_PASSWORD=

# Redis (for caching and sessions)
REDIS_URL=redis://redis:6379/0

# Security
WTF_CSRF_ENABLED=True

# Gunicorn
WORKERS=4
TIMEOUT=30
BIND=0.0.0.0:5000
EOL
    echo "✅ Environment file created: .env"
else
    echo "✅ Environment file already exists: .env"
fi

echo ""

# Check if we're in the right directory
if [ ! -f "docker-compose.yml" ]; then
    echo "❌ docker-compose.yml not found. Please run this script from the project root directory."
    exit 1
fi

# Build and start the system
echo "🔨 Building Docker images..."
if [ "$MAKE_AVAILABLE" = true ]; then
    make build
else
    docker-compose build
fi

echo ""
echo "🚀 Starting the Campus Locker System..."
if [ "$MAKE_AVAILABLE" = true ]; then
    make up
else
    docker-compose up -d
fi

echo ""
echo "⏳ Waiting for services to start..."
sleep 10

# Test the deployment
echo "🧪 Testing deployment..."
if [ "$MAKE_AVAILABLE" = true ]; then
    make test
else
    bash scripts/test-deployment.sh
fi

echo ""
echo "🎉 Setup completed successfully!"
echo ""
echo "📱 Access your application:"
echo "   🏠 Main Application: http://localhost/"
echo "   💊 Health Check: http://localhost/health"
echo "   📧 Email Testing (MailHog): http://localhost:8025"
echo "   👤 Admin Login: http://localhost/admin/login"
echo "      Username: admin"
echo "      Password: adminpass123"
echo ""
echo "📚 Quick commands:"
if [ "$MAKE_AVAILABLE" = true ]; then
    echo "   make logs       # View application logs"
    echo "   make down       # Stop the system"
    echo "   make dev-up     # Start development mode"
    echo "   make help       # Show all available commands"
else
    echo "   docker-compose logs     # View application logs"
    echo "   docker-compose down     # Stop the system"
    echo "   docker-compose -f docker-compose.dev.yml up -d  # Start development mode"
fi
echo ""
echo "📖 Documentation:"
echo "   - README.md for complete documentation"
echo "   - QUICK_START.md for quick reference"
echo "   - DOCKER_DEPLOYMENT.md for detailed deployment guide"
echo ""
echo "🚀 Campus Locker System v2.0 is ready to use!" 