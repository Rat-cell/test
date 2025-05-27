# 🐳 Campus Locker System - Docker Deployment Guide

This guide covers deploying the Campus Locker System using Docker containers with a complete production-ready setup.

## 📋 Prerequisites

- **Docker** (version 20.10+)
- **Docker Compose** (version 2.0+)
- **Make** (optional, for convenience commands)
- **curl** (for testing)

## 🏗️ Architecture Overview

The Docker deployment includes:

- **🚀 Flask Application** (Gunicorn + Python 3.12)
- **🔄 Nginx Reverse Proxy** (Load balancing, SSL termination)
- **📧 MailHog** (Email testing service)
- **🗄️ SQLite Database** (Persistent storage)
- **⚡ Redis** (Caching and sessions)

## 🚀 Quick Start

### 1. Build and Start Services

```bash
# Using Make (recommended)
make build
make up

# Or using Docker Compose directly
docker-compose build
docker-compose up -d
```

### 2. Test Deployment

```bash
# Run comprehensive tests
make test

# Or quick health check
make quick-test

# Or manual testing
curl http://localhost/health
```

### 3. Access Services

- **🌐 Main Application**: http://localhost
- **📧 MailHog Web UI**: http://localhost:8025
- **🏥 Health Check**: http://localhost/health
- **👤 Admin Login**: http://localhost/admin/login

## 🛠️ Development Deployment

For development with live code reloading:

```bash
# Start development environment
make dev-up

# View logs
make dev-logs

# Stop development environment
make dev-down
```

## 📊 Service Details

### Main Application Container
- **Image**: Custom Python 3.12 slim
- **Port**: 5000 (internal), 80 (external via Nginx)
- **Features**: Gunicorn WSGI server, health checks, non-root user
- **Volumes**: Logs, database, instance data

### Nginx Reverse Proxy
- **Image**: nginx:alpine
- **Ports**: 80 (HTTP), 443 (HTTPS ready)
- **Features**: Load balancing, compression, security headers
- **Configuration**: `/nginx.conf`

### MailHog Email Service
- **Image**: mailhog/mailhog:v1.0.1
- **Ports**: 1025 (SMTP), 8025 (Web UI)
- **Purpose**: Email testing and development

### Redis Cache
- **Image**: redis:7-alpine
- **Port**: 6379
- **Purpose**: Session storage and caching
- **Persistence**: Volume-backed

## 🔧 Configuration

### Environment Variables

The application supports these environment variables:

```bash
# Flask Configuration
FLASK_ENV=production
SECRET_KEY=your-super-secret-key

# Database (SQLite)
DATABASE_URL=sqlite:///instance/campus_locker.db

# Email Configuration
MAIL_SERVER=mailhog
MAIL_PORT=1025
MAIL_DEFAULT_SENDER=noreply@campuslocker.local

# Application Settings
PARCEL_MAX_PICKUP_DAYS=7
PARCEL_DEFAULT_PIN_VALIDITY_DAYS=7
ENABLE_LOCKER_SENSOR_DATA_FEATURE=true

# Logging
LOG_LEVEL=INFO
LOG_FILE=/app/logs/campus_locker.log
```

### Customizing Configuration

1. **Edit `docker-compose.yml`** for production settings
2. **Edit `docker-compose.dev.yml`** for development settings
3. **Modify `nginx.conf`** for proxy configuration

## 🧪 Testing the Deployment

### Automated Testing

```bash
# Full test suite
make test

# Quick health check
make quick-test
```

### Manual Testing

```bash
# Test health endpoint
curl -f http://localhost/health

# Test main pages
curl -f http://localhost/deposit
curl -f http://localhost/pickup
curl -f http://localhost/admin/login

# Test MailHog
curl -f http://localhost:8025
```

### Expected Responses

**Health Check** (`/health`):
```json
{
  "status": "healthy",
  "service": "campus-locker-system",
  "version": "1.0.0"
}
```

## 📋 Available Make Commands

```bash
make help          # Show all available commands
make build          # Build Docker images
make up             # Start production deployment
make down           # Stop production deployment
make logs           # View production logs
make test           # Test deployment
make clean          # Clean up Docker resources

# Development commands
make dev-up         # Start development deployment
make dev-down       # Stop development deployment
make dev-logs       # View development logs
```

## 🔍 Monitoring and Logs

### View Logs

```bash
# All services
make logs

# Specific service
docker-compose logs -f app
docker-compose logs -f nginx
docker-compose logs -f mailhog
```

### Health Monitoring

```bash
# Check container health
docker ps

# Inspect specific container health
docker inspect campus_locker_app --format='{{.State.Health.Status}}'
```

## 🛡️ Security Features

- **Non-root containers**: All services run as non-root users
- **Security headers**: Nginx adds security headers
- **Health checks**: All services have health monitoring
- **Network isolation**: Services communicate via Docker network
- **Volume permissions**: Proper file permissions and ownership

## 🔧 Troubleshooting

### Common Issues

**Port conflicts:**
```bash
# Check what's using port 80
sudo lsof -i :80

# Use different ports if needed
# Edit docker-compose.yml ports section
```

**Permission issues:**
```bash
# Fix volume permissions
sudo chown -R $USER:$USER ./logs ./instance
```

**Container won't start:**
```bash
# Check logs
docker-compose logs app

# Check health status
docker inspect campus_locker_app
```

**Database issues:**
```bash
# Reset database
docker-compose down -v
docker-compose up -d
```

### Debug Mode

For debugging, use the development deployment:

```bash
make dev-up
make dev-logs
```

## 🚀 Production Deployment

### SSL/HTTPS Setup

1. **Generate SSL certificates**:
```bash
mkdir ssl
# Add your SSL certificates to ./ssl/
```

2. **Update nginx.conf**:
   - Uncomment SSL configuration
   - Update certificate paths
   - Enable HTTPS redirect

3. **Update docker-compose.yml**:
   - Mount SSL certificates
   - Update environment variables

### Performance Tuning

1. **Scale application containers**:
```bash
docker-compose up -d --scale app=3
```

2. **Adjust Gunicorn workers**:
   - Edit `Dockerfile` CMD line
   - Increase `--workers` count

3. **Configure Redis persistence**:
   - Update Redis configuration
   - Enable RDB snapshots

## 📚 Additional Resources

- [Docker Documentation](https://docs.docker.com/)
- [Docker Compose Reference](https://docs.docker.com/compose/)
- [Nginx Configuration Guide](https://nginx.org/en/docs/)
- [Flask Deployment Options](https://flask.palletsprojects.com/en/2.3.x/deploying/)

## 🆘 Support

If you encounter issues:

1. Check the logs: `make logs`
2. Run health tests: `make test`
3. Verify Docker setup: `docker --version && docker-compose --version`
4. Check port availability: `netstat -tulpn | grep :80`

---

**🎉 Your Campus Locker System is now containerized and ready for production deployment!** 