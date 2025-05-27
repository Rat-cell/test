# Campus Locker System v2.0 - Team I

## 🚀 Version 2.0 - Production-Ready Docker Deployment

**Campus Locker System** is now fully containerized and production-ready! Version 2.0 introduces comprehensive Docker deployment with enterprise-grade features including reverse proxy, email testing, caching, and automated health monitoring.

### 🎯 What's New in v2.0

- **🐳 Full Docker Containerization**: Production and development environments
- **🔄 Nginx Reverse Proxy**: Load balancing, security headers, SSL-ready
- **📧 Integrated Email Testing**: MailHog for development and testing
- **⚡ Redis Caching**: Session storage and performance optimization
- **🏥 Health Monitoring**: Automated health checks and service dependencies
- **🔒 Security Hardened**: Non-root containers, security headers, proper secrets management
- **📊 Comprehensive Logging**: Structured logging with rotation and monitoring
- **🧪 Enhanced Testing**: Containerized test environment with 91 passing tests
- **📚 Complete Documentation**: Deployment guides, troubleshooting, and best practices

---

## 📋 Table of Contents

1. [Quick Start (Docker)](#quick-start-docker)
2. [Project Overview](#project-overview)
3. [Docker Deployment](#docker-deployment)
4. [Development Setup](#development-setup)
5. [Architecture & Features](#architecture--features)
6. [Testing](#testing)
7. [Configuration](#configuration)
8. [Troubleshooting](#troubleshooting)
9. [Legacy Local Setup](#legacy-local-setup)

---

## 🚀 Quick Start (Docker)

Get the Campus Locker System running in under 5 minutes:

### Prerequisites
- **Docker Desktop** (macOS/Windows) or **Docker Engine** (Linux)
- **Docker Compose** (included with Docker Desktop)
- **Git** for cloning the repository

### 1. Clone and Navigate
```bash
git clone <repository-url>
cd campus_locker_system
```

### 2. Start Production Environment
```bash
make up
```

### 3. Access the Application
- **🏠 Main Application**: http://localhost/
- **💊 Health Check**: http://localhost/health
- **📧 Email Testing (MailHog)**: http://localhost:8025
- **🔧 Direct App Access**: http://localhost:5001

### 4. Test the System
```bash
make test
```

That's it! The system is now running with all services containerized and ready for use.

---

## 📖 Project Overview

### Purpose
The Campus Locker System is a browser-based parcel management solution that enables 24/7 secure parcel deposits and pickups using one-time PINs. Perfect for universities, offices, and residential complexes.

### Technology Stack
- **Backend**: Python 3.12, Flask, SQLAlchemy
- **Database**: SQLite with audit logging
- **Frontend**: HTML templates with responsive design
- **Containerization**: Docker, Docker Compose
- **Reverse Proxy**: Nginx with security headers
- **Caching**: Redis for sessions and performance
- **Email Testing**: MailHog for development
- **Testing**: Pytest with 91 comprehensive tests

### Team
Developed by **Team I**: Pauline Feldhoff, Paul von Franqué, Asma Mzee, Samuel Neo, Gublan Dag as part of the Digital Literacy IV: Software Architecture course.

---

## 🐳 Docker Deployment

### Architecture Overview

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│     Nginx       │    │   Flask App     │    │     Redis       │
│  Reverse Proxy  │────│  (Gunicorn)     │────│     Cache       │
│   Port 80/443   │    │   Port 5000     │    │   Port 6379     │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         │              ┌─────────────────┐              │
         └──────────────│    MailHog      │──────────────┘
                        │ Email Testing   │
                        │ Port 1025/8025  │
                        └─────────────────┘
```

### Available Environments

#### 🏭 Production Environment
- **Purpose**: Production-ready deployment with Gunicorn, Nginx, and Redis
- **Command**: `make up`
- **Features**: 
  - Gunicorn WSGI server with 4 workers
  - Nginx reverse proxy with security headers
  - Redis caching and session storage
  - Health monitoring and auto-restart
  - Persistent data volumes

#### 🛠️ Development Environment  
- **Purpose**: Development with live code reloading
- **Command**: `make dev-up`
- **Features**:
  - Flask development server with debug mode
  - Live code mounting for instant changes
  - Simplified configuration
  - Debug logging enabled

### Quick Commands

```bash
# Production Environment
make build          # Build Docker images
make up             # Start production deployment
make down           # Stop production deployment
make logs           # View production logs
make test           # Test deployment

# Development Environment
make dev-up         # Start development deployment
make dev-down       # Stop development deployment
make dev-logs       # View development logs

# Maintenance
make clean          # Clean up Docker resources
make help           # Show all available commands
```

### Service Details

#### 🌐 Nginx Reverse Proxy
- **Image**: nginx:alpine
- **Ports**: 80 (HTTP), 443 (HTTPS ready)
- **Features**:
  - Load balancing and reverse proxy
  - Security headers (X-Frame-Options, X-Content-Type-Options, etc.)
  - Gzip compression
  - SSL/HTTPS ready (certificates required for production)
  - Health check routing

#### 🐍 Flask Application
- **Image**: Custom Python 3.12 slim
- **Ports**: 5001 (external), 5000 (internal)
- **Features**:
  - Gunicorn WSGI server with 4 workers
  - Non-root user for security
  - Health check endpoint
  - Persistent database and logs
  - Environment-based configuration

#### ⚡ Redis Cache
- **Image**: redis:7-alpine
- **Port**: 6379
- **Purpose**: Session storage and caching
- **Features**:
  - Persistent data storage
  - Health monitoring
  - Memory optimization

#### 📧 MailHog Email Testing
- **Image**: mailhog/mailhog:v1.0.1
- **Ports**: 1025 (SMTP), 8025 (Web UI)
- **Purpose**: Email testing and development
- **Features**:
  - Catches all outbound emails
  - Web interface for viewing emails
  - No external email dependencies

### Data Persistence

All important data is stored in Docker volumes for persistence across container restarts:

- **`app_databases`**: SQLite database files
- **`app_logs`**: Application log files
- **`redis_data`**: Redis cache and session data
- **`app_data`**: Additional application data

### Environment Variables

The system supports comprehensive configuration through environment variables:

```bash
# Flask Configuration
FLASK_ENV=production
SECRET_KEY=your-super-secret-key

# Database Configuration
DATABASE_URL=sqlite:////app/databases/campus_locker.db
AUDIT_DATABASE_URL=sqlite:////app/databases/campus_locker_audit.db

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

---

## 🛠️ Development Setup

### Option 1: Docker Development (Recommended)

Perfect for consistent development environment:

```bash
# Start development environment
make dev-up

# View logs
make dev-logs

# Run tests in container
docker-compose -f docker-compose.dev.yml exec app pytest

# Stop development environment
make dev-down
```

### Option 2: VS Code with Remote Containers

For advanced development with full IDE integration:

1. Install the **Remote - Containers** extension in VS Code
2. Open the project folder in VS Code
3. Press `Ctrl+Shift+P` (or `Cmd+Shift+P` on Mac)
4. Select "Remote-Containers: Reopen in Container"
5. VS Code will build and connect to the development container

### Option 3: Local Development

For traditional local development (see [Legacy Local Setup](#legacy-local-setup))

---

## 🏗️ Architecture & Features

### Hexagonal Architecture

The system follows hexagonal (ports and adapters) architecture principles:

```
┌─────────────────────────────────────────────────────────────┐
│                    Presentation Layer                       │
│  ┌─────────────────┐  ┌─────────────────┐  ┌──────────────┐ │
│  │   Web Routes    │  │   API Routes    │  │  Templates   │ │
│  │   (routes.py)   │  │ (api_routes.py) │  │   (HTML)     │ │
│  └─────────────────┘  └─────────────────┘  └──────────────┘ │
└─────────────────────────────────────────────────────────────┘
                                │
┌─────────────────────────────────────────────────────────────┐
│                     Service Layer                           │
│  ┌─────────────────┐  ┌─────────────────┐  ┌──────────────┐ │
│  │ Parcel Service  │  │  Admin Service  │  │ Audit Service│ │
│  │   (services/)   │  │   (services/)   │  │  (services/) │ │
│  └─────────────────┘  └─────────────────┘  └──────────────┘ │
└─────────────────────────────────────────────────────────────┘
                                │
┌─────────────────────────────────────────────────────────────┐
│                    Business Layer                           │
│  ┌─────────────────┐  ┌─────────────────┐  ┌──────────────┐ │
│  │ Business Logic  │  │   PIN Manager   │  │   Entities   │ │
│  │  (business/)    │  │  (business/)    │  │ (business/)  │ │
│  └─────────────────┘  └─────────────────┘  └──────────────┘ │
└─────────────────────────────────────────────────────────────┘
                                │
┌─────────────────────────────────────────────────────────────┐
│                   Persistence Layer                         │
│  ┌─────────────────┐  ┌─────────────────┐  ┌──────────────┐ │
│  │     Models      │  │   Repositories  │  │    Mappers   │ │
│  │ (persistence/)  │  │ (persistence/)  │  │(persistence/)│ │
│  └─────────────────┘  └─────────────────┘  └──────────────┘ │
└─────────────────────────────────────────────────────────────┘
                                │
┌─────────────────────────────────────────────────────────────┐
│                     Adapters Layer                          │
│  ┌─────────────────┐  ┌─────────────────┐  ┌──────────────┐ │
│  │Database Adapter │  │  Email Adapter  │  │ Audit Adapter│ │
│  │  (adapters/)    │  │  (adapters/)    │  │ (adapters/)  │ │
│  └─────────────────┘  └─────────────────┘  └──────────────┘ │
└─────────────────────────────────────────────────────────────┘
                                │
┌─────────────────────────────────────────────────────────────┐
│                    Database Layer                           │
│  ┌─────────────────┐  ┌─────────────────┐  ┌──────────────┐ │
│  │   SQLite DB     │  │   Audit DB      │  │  File System │ │
│  │ (campus_locker  │  │(campus_locker   │  │    (logs)    │ │
│  │     .db)        │  │   _audit.db)    │  │              │ │
│  └─────────────────┘  └─────────────────┘  └──────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

### Core Features

#### 📦 Parcel Management
- **Deposit**: Automated locker assignment based on parcel size
- **PIN Generation**: Secure 6-digit PIN with SHA-256 hashing
- **Email Notifications**: Automatic PIN delivery to recipients
- **Pickup Process**: PIN validation with expiry checking
- **Status Tracking**: Complete parcel lifecycle management

#### 🔐 Security Features
- **Secure PIN Storage**: Salted SHA-256 hashing
- **Admin Authentication**: Bcrypt password hashing
- **Non-root Containers**: Security-hardened Docker images
- **Security Headers**: Comprehensive HTTP security headers
- **Input Validation**: Robust form and API validation

#### 👨‍💼 Admin Features
- **Dashboard**: Overview of system status and metrics
- **Locker Management**: Status control and maintenance mode
- **Audit Logging**: Comprehensive activity tracking
- **Parcel Oversight**: Manual intervention capabilities
- **User Management**: Admin account administration

#### 🔌 API Endpoints
- **Health Check**: `GET /health` - System health status
- **Parcel Operations**: RESTful API for parcel management
- **Locker Integration**: Hardware integration endpoints
- **Sensor Data**: IoT sensor data collection
- **Audit Access**: Programmatic audit log access

#### 📊 Monitoring & Logging
- **Health Checks**: Automated service monitoring
- **Structured Logging**: JSON-formatted logs with rotation
- **Audit Trail**: Complete activity tracking
- **Performance Metrics**: Response time and error tracking
- **Email Monitoring**: Delivery status tracking

### Database Schema

#### Main Database (`campus_locker.db`)
- **`locker`**: Physical locker information and status
- **`parcel`**: Parcel details and lifecycle tracking
- **`admin_user`**: Administrator account management
- **`locker_sensor_data`**: IoT sensor data collection

#### Audit Database (`campus_locker_audit.db`)
- **`audit_log`**: Comprehensive activity and security logging

---

## 🧪 Testing

### Test Suite Overview

The system includes **91 comprehensive tests** covering:

- **Unit Tests**: Individual component testing
- **Integration Tests**: Service interaction testing
- **API Tests**: Endpoint functionality and error handling
- **Edge Case Tests**: Boundary conditions and error scenarios
- **Security Tests**: Authentication and authorization
- **Database Tests**: Data persistence and integrity

### Running Tests

#### Docker Environment (Recommended)
```bash
# Run all tests
make test

# Run tests with coverage
docker-compose exec app pytest --cov=app

# Run specific test categories
docker-compose exec app pytest tests/test_application.py
docker-compose exec app pytest tests/edge_cases/
```

#### Local Environment
```bash
# Activate virtual environment
source venv/bin/activate

# Run all tests
pytest

# Run with coverage
pytest --cov=app

# Run specific tests
pytest tests/test_presentation.py -v
```

### Test Categories

#### Core Functionality Tests
- **Parcel Deposit Flow**: Complete deposit process validation
- **PIN Generation**: Security and uniqueness verification
- **Pickup Process**: PIN validation and expiry handling
- **Email Notifications**: Delivery and content verification

#### Edge Case Tests
- **Invalid PIN Scenarios**: Wrong PIN, expired PIN, reused PIN
- **Locker Status Edge Cases**: Out of service, disputed contents
- **API Error Handling**: Invalid requests, missing data
- **Concurrent Operations**: Race condition handling

#### Security Tests
- **Authentication**: Login/logout functionality
- **Authorization**: Access control verification
- **PIN Security**: Hash validation and timing attacks
- **Input Validation**: SQL injection and XSS prevention

### Continuous Integration

The test suite is designed for CI/CD integration:

```yaml
# Example GitHub Actions workflow
name: Test Suite
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Run tests
        run: |
          make build
          make test
```

---

## ⚙️ Configuration

### Environment Configuration

The system supports multiple configuration methods:

#### 1. Environment Variables
```bash
# Production settings
export FLASK_ENV=production
export SECRET_KEY=your-production-secret
export DATABASE_URL=sqlite:////app/databases/campus_locker.db
```

#### 2. Docker Compose Override
Create `docker-compose.override.yml`:
```yaml
version: '3.8'
services:
  app:
    environment:
      - SECRET_KEY=your-custom-secret
      - PARCEL_MAX_PICKUP_DAYS=14
```

#### 3. Configuration Files
Modify `campus_locker_system/app/config.py` for advanced settings.

### Key Configuration Options

#### Application Settings
- **`SECRET_KEY`**: Flask secret key for sessions and security
- **`PARCEL_MAX_PICKUP_DAYS`**: Maximum days for parcel pickup (default: 7)
- **`PARCEL_DEFAULT_PIN_VALIDITY_DAYS`**: PIN validity period (default: 7)
- **`ENABLE_LOCKER_SENSOR_DATA_FEATURE`**: Enable IoT sensor integration

#### Database Settings
- **`DATABASE_URL`**: Main database connection string
- **`AUDIT_DATABASE_URL`**: Audit database connection string
- **`SQLALCHEMY_DATABASE_URI`**: SQLAlchemy database URI

#### Email Settings
- **`MAIL_SERVER`**: SMTP server hostname
- **`MAIL_PORT`**: SMTP server port
- **`MAIL_USE_TLS`**: Enable TLS encryption
- **`MAIL_DEFAULT_SENDER`**: Default sender email address

#### Logging Settings
- **`LOG_LEVEL`**: Logging level (DEBUG, INFO, WARNING, ERROR)
- **`LOG_FILE`**: Log file path
- **`LOG_DIR`**: Log directory path

### Production Configuration

For production deployment:

1. **Generate Strong Secret Key**:
```python
import secrets
print(secrets.token_hex(32))
```

2. **Configure SSL Certificates**:
```bash
# Place certificates in ssl/ directory
mkdir ssl
cp your-cert.pem ssl/cert.pem
cp your-key.pem ssl/key.pem
```

3. **Enable HTTPS in nginx.conf**:
Uncomment the SSL server block and configure certificates.

4. **Set Production Environment Variables**:
```bash
export FLASK_ENV=production
export SECRET_KEY=your-generated-secret-key
export DATABASE_URL=your-production-database-url
```

---

## 🔧 Troubleshooting

### Common Issues

#### Port Conflicts
**Problem**: Port 5000 already in use (macOS Control Center)
**Solution**: The system automatically uses port 5001 externally
```bash
# Access application on port 5001
curl http://localhost:5001/health
```

#### Container Startup Issues
**Problem**: Containers fail to start or restart continuously
**Solution**: Check logs and dependencies
```bash
# Check container status
docker ps -a

# View container logs
docker logs campus_locker_app
docker logs campus_locker_nginx

# Restart specific service
docker-compose restart app
```

#### Database Permission Issues
**Problem**: SQLite database permission errors
**Solution**: Ensure proper volume mounting and permissions
```bash
# Check volume status
docker volume ls

# Recreate volumes if needed
make down
docker volume rm test_app_databases
make up
```

#### SSL/HTTPS Issues
**Problem**: Nginx SSL configuration errors
**Solution**: SSL is disabled by default for development
```bash
# For development, use HTTP
curl http://localhost/health

# For production, configure SSL certificates
# See Configuration section for SSL setup
```

### Health Check Endpoints

Monitor system health using built-in endpoints:

```bash
# Application health
curl http://localhost/health
# Response: {"service":"campus-locker-system","status":"healthy","version":"2.0.0"}

# Individual service health
curl http://localhost:5001/health  # Direct app access
curl http://localhost:8025         # MailHog web interface
```

### Log Analysis

Access logs for debugging:

```bash
# Application logs
make logs

# Specific service logs
docker logs campus_locker_app
docker logs campus_locker_nginx
docker logs campus_locker_redis
docker logs campus_locker_mailhog

# Follow logs in real-time
docker logs -f campus_locker_app
```

### Performance Optimization

#### Database Optimization
```bash
# Monitor database size
docker exec campus_locker_app ls -la /app/databases/

# Backup databases
docker cp campus_locker_app:/app/databases/ ./backup/
```

#### Memory Usage
```bash
# Monitor container resource usage
docker stats

# Optimize Redis memory
docker exec campus_locker_redis redis-cli info memory
```

### Recovery Procedures

#### Complete System Reset
```bash
# Stop all services
make down

# Remove all data (WARNING: This deletes all data!)
docker volume rm test_app_databases test_app_logs test_redis_data

# Rebuild and restart
make build
make up
```

#### Backup and Restore
```bash
# Backup data volumes
docker run --rm -v test_app_databases:/data -v $(pwd):/backup alpine tar czf /backup/databases.tar.gz -C /data .

# Restore data volumes
docker run --rm -v test_app_databases:/data -v $(pwd):/backup alpine tar xzf /backup/databases.tar.gz -C /data
```

---

## 📚 Legacy Local Setup

> **Note**: Docker deployment is recommended for most use cases. Use local setup only for advanced development or debugging.

### Prerequisites
- Python 3.7+
- pip (Python package installer)
- Virtual environment support

### Setup Steps

1. **Clone Repository**:
```bash
git clone <repository-url>
cd campus_locker_system
```

2. **Create Virtual Environment**:
```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install Dependencies**:
```bash
pip install -r requirements.txt
```

4. **Database Setup**:
```bash
# Databases are created automatically on first run
# Located in: campus_locker_system/databases/
```

5. **Create Admin User**:
```bash
cd campus_locker_system
python create_admin.py admin adminpass123
```

6. **Start MailHog** (for email testing):
```bash
# Using Docker (recommended)
docker run -d -p 1025:1025 -p 8025:8025 mailhog/mailhog

# Or download binary from GitHub releases
```

7. **Run Application**:
```bash
python run.py
```

8. **Access Application**:
- Main app: http://127.0.0.1:5000/
- MailHog: http://localhost:8025

### Local Development Workflow

```bash
# Activate environment
source venv/bin/activate

# Run tests
pytest

# Run with debug mode
export FLASK_DEBUG=1
python run.py

# Deactivate environment
deactivate
```

---

## 📄 License & Contributing

### License
This project is developed as part of an academic course. Please respect intellectual property and academic integrity guidelines.

### Contributing
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Ensure all tests pass
6. Submit a pull request

### Development Guidelines
- Follow PEP 8 style guidelines
- Write comprehensive tests
- Update documentation
- Use meaningful commit messages
- Maintain backward compatibility

---

## 🎯 Roadmap & Future Enhancements

### Planned Features
- **Kubernetes Deployment**: Orchestration for large-scale deployments
- **PostgreSQL Support**: Production-grade database option
- **SMS Notifications**: Alternative to email notifications
- **Mobile App**: Native mobile application
- **IoT Integration**: Real hardware locker integration
- **Analytics Dashboard**: Usage statistics and reporting
- **Multi-tenant Support**: Multiple organization support

### Performance Improvements
- **Caching Strategy**: Advanced Redis caching patterns
- **Database Optimization**: Query optimization and indexing
- **CDN Integration**: Static asset delivery optimization
- **Load Balancing**: Multi-instance deployment support

### Security Enhancements
- **OAuth Integration**: Third-party authentication
- **API Rate Limiting**: DDoS protection
- **Audit Encryption**: Encrypted audit logs
- **Compliance Features**: GDPR and privacy compliance

---

## 📞 Support & Contact

### Documentation
- **Deployment Guide**: See `DOCKER_DEPLOYMENT.md`
- **API Documentation**: Available at `/api/docs` when running
- **Architecture Guide**: See `docs/architecture.md`

### Getting Help
1. Check the [Troubleshooting](#troubleshooting) section
2. Review container logs: `make logs`
3. Test system health: `make test`
4. Consult the development team

### Team Contact
**Team I - Digital Literacy IV: Software Architecture**
- Pauline Feldhoff
- Paul von Franqué  
- Asma Mzee
- Samuel Neo
- Gublan Dag

---

## 📚 Appendices

### Appendix A: Version History & Changelog

#### Version 2.0.0 (Current) - Docker Production Deployment
**Release Date**: December 2024

**🎯 Major Features:**
- **🐳 Full Docker Containerization**: Production and development environments
- **🔄 Nginx Reverse Proxy**: Load balancing, security headers, SSL-ready
- **📧 Integrated Email Testing**: MailHog for development and testing
- **⚡ Redis Caching**: Session storage and performance optimization
- **🏥 Health Monitoring**: Automated health checks and service dependencies
- **🔒 Security Hardened**: Non-root containers, security headers, proper secrets management
- **📊 Comprehensive Logging**: Structured logging with rotation and monitoring
- **🧪 Enhanced Testing**: Containerized test environment with 91 passing tests
- **📚 Complete Documentation**: Deployment guides, troubleshooting, and best practices

**🏗️ Architecture Improvements:**
- Complete hexagonal architecture implementation
- 6 distinct business domains (Parcel, Locker, PIN, Notification, Admin, Audit)
- Clean separation of concerns with adapters pattern
- Repository pattern for data access
- Service layer orchestration

**🔧 Technical Enhancements:**
- Python 3.12 support
- Gunicorn WSGI server with 4 workers
- Nginx reverse proxy with security headers
- Redis for caching and session management
- SQLite with audit database separation
- Comprehensive health checks
- Docker Compose for orchestration
- Makefile for deployment automation

**🛡️ Security Improvements:**
- Non-root container execution
- Security headers implementation
- Proper secrets management
- Input validation and sanitization
- Audit logging enhancement

**📋 Migration Notes:**
- Migrated from monolithic Flask app to hexagonal architecture
- Database path updated for containerization
- Port configuration changed (5001 external, 5000 internal)
- Environment variable configuration
- Volume-based data persistence

---

#### Version 1.0.0 - Hexagonal Architecture Foundation
**Release Date**: November 2024

**🎯 Major Features:**
- Complete hexagonal architecture migration
- 91 comprehensive tests (100% passing)
- 6 business domain extraction
- Clean adapter pattern implementation
- Professional CI/CD pipeline

**🏗️ Architecture Migration:**
- **Phase 1**: Repository skeleton with proper folder layout
- **Phase 2**: Domain extraction into 6 domains
- **Phase 3**: Adapter implementation (SQL, MailHog)
- **Phase 4**: CI & tests with GitHub Actions pipeline
- **Phase 5**: Code cleanup and legacy removal

**📦 Business Domains:**
1. **Parcel Management**: Deposit, pickup, tracking, dispute handling
2. **Locker Management**: Status control, availability, maintenance
3. **PIN Management**: Generation, validation, expiry, reissue
4. **Notification Management**: Email templates, delivery orchestration
5. **Admin & Authentication**: Login, sessions, permissions
6. **Audit Logging**: Activity tracking, security logging

**🔌 Adapters Implemented:**
- **Email Adapter**: Flask-Mail abstraction with mock testing
- **Database Adapter**: SQLAlchemy repository pattern
- **Audit Adapter**: Centralized logging with retention policies

**🧪 Testing Excellence:**
- 91 comprehensive tests covering all domains
- Unit, integration, and edge case testing
- Security and authentication testing
- CI/CD pipeline with multi-Python version support
- Code quality checks (flake8, black, isort)
- Security scanning (safety, bandit)
- 85% minimum coverage threshold

---

#### Version 0.9.0 - Legacy Monolithic Application
**Release Date**: October 2024

**🎯 Core Features:**
- Basic Flask web application
- Parcel deposit and pickup functionality
- PIN-based security system
- Admin dashboard
- Email notifications
- SQLite database storage

**📋 Original Implementation:**
- Monolithic Flask application structure
- Single `services.py` file with all business logic
- Basic HTML templates
- Simple SQLite database
- Flask-Mail for email notifications
- Basic admin authentication

**🔧 Technical Stack:**
- Python 3.7+
- Flask web framework
- SQLAlchemy ORM
- SQLite database
- Flask-Mail for emails
- HTML/CSS frontend
- Basic logging

**📊 Features:**
- Parcel deposit with automatic locker assignment
- 6-digit PIN generation and validation
- Email notifications to recipients
- Admin dashboard for system management
- Locker status management
- Basic audit logging
- Pickup process with PIN validation

---

### Appendix B: Original README (v1.0.0 - Pre-Docker)

> **Note**: This is the complete original README content that existed before Docker containerization was implemented.

# Campus Locker System - Team I

## Overview

The Campus Locker System is a browser-based parcel management solution that enables 24/7 secure parcel deposits and pickups using one-time PINs. This system is designed for universities, offices, and residential complexes to automate parcel handling.

## Team Members
- **Pauline Feldhoff**
- **Paul von Franqué**
- **Asma Mzee**
- **Samuel Neo**
- **Gublan Dag**

*Digital Literacy IV: Software Architecture Course Project*

## Features

### Core Functionality
- **Parcel Deposit**: Automated locker assignment based on parcel size
- **PIN-based Security**: 6-digit one-time PIN generation with SHA-256 hashing
- **Email Notifications**: Automatic delivery of pickup instructions to recipients
- **Admin Dashboard**: Comprehensive system management and oversight
- **Audit Logging**: Complete activity tracking for security and compliance
- **Locker Management**: Real-time status monitoring and control

### Security Features
- **Secure PIN Storage**: Salted SHA-256 hashing for PIN protection
- **Admin Authentication**: Bcrypt password hashing for admin accounts
- **Input Validation**: Comprehensive form and API validation
- **Session Management**: Secure session handling
- **Audit Trail**: Complete activity logging for security monitoring

### Admin Features
- **System Dashboard**: Overview of locker status and system metrics
- **Locker Control**: Manual locker status management and maintenance mode
- **Parcel Oversight**: Manual intervention capabilities for disputed parcels
- **User Management**: Admin account creation and management
- **Audit Review**: Access to comprehensive system logs

## Quick Start

### Prerequisites
- **Python 3.7+**
- **pip** (Python package installer)
- **Virtual environment** support
- **MailHog** for email testing (optional but recommended)

### Installation Steps

1. **Clone the Repository**:
   ```bash
   git clone <repository-url>
   cd campus_locker_system
   ```

2. **Set Up Virtual Environment**:
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Set Up Email Testing (MailHog)**:
   ```bash
   # Option 1: Using Docker (recommended)
   docker run -d -p 1025:1025 -p 8025:8025 mailhog/mailhog
   
   # Option 2: Download binary from GitHub releases
   # https://github.com/mailhog/MailHog/releases
   ```

5. **Initialize Database and Create Admin**:
   ```bash
   cd campus_locker_system
   python create_admin.py admin adminpass123
   ```

6. **Run the Application**:
   ```bash
   python run.py
   ```

7. **Access the System**:
   - **Main Application**: http://127.0.0.1:5000/
   - **Admin Dashboard**: http://127.0.0.1:5000/admin/login
   - **MailHog Interface**: http://localhost:8025

## Architecture

The system follows **Hexagonal Architecture** (Ports and Adapters) principles:

```
┌─────────────────────────────────────────────────────────────┐
│                    Presentation Layer                       │
│  ┌─────────────────┐  ┌─────────────────┐  ┌──────────────┐ │
│  │   Web Routes    │  │   API Routes    │  │  Templates   │ │
│  │   (routes.py)   │  │ (api_routes.py) │  │   (HTML)     │ │
│  └─────────────────┘  └─────────────────┘  └──────────────┘ │
└─────────────────────────────────────────────────────────────┘
                                │
┌─────────────────────────────────────────────────────────────┐
│                     Service Layer                           │
│  ┌─────────────────┐  ┌─────────────────┐  ┌──────────────┐ │
│  │ Parcel Service  │  │  Admin Service  │  │ Audit Service│ │
│  │   (services/)   │  │   (services/)   │  │  (services/) │ │
│  └─────────────────┘  └─────────────────┘  └──────────────┘ │
└─────────────────────────────────────────────────────────────┘
                                │
┌─────────────────────────────────────────────────────────────┐
│                    Business Layer                           │
│  ┌─────────────────┐  ┌─────────────────┐  ┌──────────────┐ │
│  │ Business Logic  │  │   PIN Manager   │  │   Entities   │ │
│  │  (business/)    │  │  (business/)    │  │ (business/)  │ │
│  └─────────────────┘  └─────────────────┘  └──────────────┘ │
└─────────────────────────────────────────────────────────────┘
                                │
┌─────────────────────────────────────────────────────────────┐
│                   Persistence Layer                         │
│  ┌─────────────────┐  ┌─────────────────┐  ┌──────────────┐ │
│  │     Models      │  │   Repositories  │  │    Mappers   │ │
│  │ (persistence/)  │  │ (persistence/)  │  │(persistence/)│ │
│  └─────────────────┘  └─────────────────┘  └──────────────┘ │
└─────────────────────────────────────────────────────────────┘
                                │
┌─────────────────────────────────────────────────────────────┐
│                     Adapters Layer                          │
│  ┌─────────────────┐  ┌─────────────────┐  ┌──────────────┐ │
│  │Database Adapter │  │  Email Adapter  │  │ Audit Adapter│ │
│  │  (adapters/)    │  │  (adapters/)    │  │ (adapters/)  │ │
│  └─────────────────┘  └─────────────────┘  └──────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

### Business Domains

1. **Parcel Management**: Deposit, pickup, tracking, dispute handling
2. **Locker Management**: Status control, availability, maintenance
3. **PIN Management**: Generation, validation, expiry, reissue
4. **Notification Management**: Email templates, delivery orchestration
5. **Admin & Authentication**: Login, sessions, permissions
6. **Audit Logging**: Activity tracking, security logging

## Testing

The system includes **91 comprehensive tests** covering all aspects:

### Running Tests
```bash
# Run all tests
pytest

# Run with coverage report
pytest --cov=app

# Run specific test categories
pytest tests/test_application.py
pytest tests/edge_cases/
pytest tests/test_presentation.py

# Run tests with verbose output
pytest -v
```

### Test Categories
- **Unit Tests**: Individual component testing
- **Integration Tests**: Service interaction testing
- **Edge Case Tests**: Boundary conditions and error scenarios
- **Security Tests**: Authentication and authorization testing
- **API Tests**: Endpoint functionality and error handling

### Test Coverage
- **91 tests total** with 100% pass rate
- **Comprehensive coverage** of all business domains
- **Edge case testing** for robust error handling
- **Security testing** for authentication and authorization

## Configuration

### Environment Variables
```bash
# Flask Configuration
FLASK_ENV=development
FLASK_DEBUG=1
SECRET_KEY=your-secret-key-here

# Database Configuration
DATABASE_URL=sqlite:///instance/campus_locker.db
AUDIT_DATABASE_URL=sqlite:///instance/campus_locker_audit.db

# Email Configuration (MailHog)
MAIL_SERVER=localhost
MAIL_PORT=1025
MAIL_USE_TLS=False
MAIL_USE_SSL=False
MAIL_DEFAULT_SENDER=noreply@campuslocker.local

# Application Settings
PARCEL_MAX_PICKUP_DAYS=7
PARCEL_DEFAULT_PIN_VALIDITY_DAYS=7
ENABLE_LOCKER_SENSOR_DATA_FEATURE=true
DEFAULT_LOCKER_SENSOR_STATE_IF_UNAVAILABLE=false

# Logging
LOG_LEVEL=INFO
```

### Configuration Files
- **`app/config.py`**: Main application configuration
- **`pytest.ini`**: Test configuration
- **`requirements.txt`**: Python dependencies

## Development

### Project Structure
```
campus_locker_system/
├── app/
│   ├── presentation/          # Web routes and templates
│   │   ├── routes.py         # Main web routes
│   │   ├── api_routes.py     # API endpoints
│   │   ├── decorators.py     # Route decorators
│   │   └── templates/        # HTML templates
│   ├── services/             # Application orchestration
│   │   ├── parcel_service.py
│   │   ├── locker_service.py
│   │   ├── pin_service.py
│   │   ├── notification_service.py
│   │   ├── admin_auth_service.py
│   │   └── audit_service.py
│   ├── business/             # Domain models and business rules
│   │   ├── parcel.py
│   │   ├── locker.py
│   │   ├── pin.py
│   │   ├── notification.py
│   │   ├── admin_auth.py
│   │   └── audit.py
│   ├── persistence/          # Database models and repositories
│   │   ├── models.py
│   │   └── repositories.py
│   ├── adapters/             # External system adapters
│   │   ├── email_adapter.py
│   │   ├── database_adapter.py
│   │   └── audit_adapter.py
│   ├── config.py
│   └── __init__.py
├── tests/                    # Comprehensive test suite
│   ├── test_application.py
│   ├── test_presentation.py
│   ├── edge_cases/
│   └── conftest.py
├── instance/                 # Database files (auto-created)
├── logs/                     # Application logs (auto-created)
├── requirements.txt          # Python dependencies
├── run.py                   # Application entry point
├── create_admin.py          # Admin user creation script
└── pytest.ini              # Test configuration
```

### Development Workflow
```bash
# Activate virtual environment
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run tests
pytest

# Run application in debug mode
export FLASK_DEBUG=1
python run.py

# Deactivate environment when done
deactivate
```

## API Endpoints

### Public Endpoints
- **`GET /`** - Main dashboard and system overview
- **`GET /deposit`** - Parcel deposit form
- **`POST /deposit`** - Process parcel deposit
- **`GET /pickup`** - Parcel pickup form
- **`POST /pickup`** - Process parcel pickup
- **`GET /health`** - System health check

### Admin Endpoints
- **`GET /admin/login`** - Admin login form
- **`POST /admin/login`** - Process admin login
- **`GET /admin/dashboard`** - Admin dashboard
- **`GET /admin/logout`** - Admin logout
- **`POST /admin/set_locker_status`** - Set locker status
- **`POST /admin/mark_locker_emptied`** - Mark locker as emptied

### API Routes
- **`GET /api/lockers`** - Get locker status information
- **`POST /api/sensor_data`** - Submit locker sensor data
- **`GET /api/audit_logs`** - Get audit log entries

## Database Schema

### Main Database (`campus_locker.db`)
- **`locker`**: Physical locker information and status
  - id, size, status, location, sensor_data
- **`parcel`**: Parcel details and lifecycle tracking
  - id, recipient_email, pin_hash, locker_id, status, timestamps
- **`admin_user`**: Administrator account management
  - id, username, password_hash, created_at
- **`locker_sensor_data`**: IoT sensor data collection
  - id, locker_id, sensor_data, timestamp

### Audit Database (`campus_locker_audit.db`)
- **`audit_log`**: Comprehensive activity and security logging
  - id, action, details, timestamp, ip_address, user_agent

## Troubleshooting

### Common Issues

**Port 5000 already in use**:
```bash
# Find and kill process using port 5000
sudo lsof -ti:5000 | xargs kill -9

# Or use a different port
export FLASK_RUN_PORT=5001
python run.py
```

**Database permission issues**:
```bash
# Reset database files
rm campus_locker_system/instance/*.db
python run.py  # Will recreate databases automatically
```

**Email notifications not working**:
```bash
# Check if MailHog is running
curl http://localhost:8025

# Start MailHog if not running
docker run -d -p 1025:1025 -p 8025:8025 mailhog/mailhog
```

**Import errors after installation**:
```bash
# Ensure virtual environment is activated
source venv/bin/activate

# Reinstall dependencies
pip install -r requirements.txt
```

### Debug Mode
```bash
# Enable Flask debug mode
export FLASK_DEBUG=1
export FLASK_ENV=development
python run.py
```

## Contributing

### Development Guidelines
1. **Fork the repository** and create a feature branch
2. **Follow PEP 8** style guidelines for Python code
3. **Write comprehensive tests** for new functionality
4. **Update documentation** for any changes
5. **Ensure all tests pass** before submitting
6. **Use meaningful commit messages**
7. **Submit a pull request** with detailed description

### Code Quality
- Follow hexagonal architecture principles
- Maintain clean separation of concerns
- Write self-documenting code with clear variable names
- Add docstrings for all public functions and classes
- Keep functions small and focused on single responsibilities

## License

This project is developed as part of an academic course. Please respect intellectual property and academic integrity guidelines.

---

*Campus Locker System v1.0.0 - Hexagonal Architecture Implementation*  
*Team I - Digital Literacy IV: Software Architecture*

---

### Appendix C: Complete Changelog & Migration History

#### MISSION_ACCOMPLISHED.md - Hexagonal Architecture Migration Complete

**🎉 MISSION ACCOMPLISHED: Hexagonal Architecture Migration + Code Cleanup**

**✅ Complete Hexagonal Architecture Migration + Legacy Cleanup - 100% SUCCESS**

The campus locker system was successfully migrated from a basic Flask app to a professional **hexagonal architecture** with **complete legacy code cleanup** while maintaining **ALL 91 tests passing** throughout the entire process.

**📊 Final Migration Stats:**
- **Architecture**: Clean hexagonal design with proper layer separation
- **Test Coverage**: 91/91 tests passing (100% success rate)
- **Domains Extracted**: 6 complete business domains
- **Adapters Implemented**: 3 external system abstractions
- **Code Quality**: Professional CI/CD pipeline with automated testing
- **Safety**: Branch-based workflow preventing direct main pushes
- **Legacy Cleanup**: 100% complete - all legacy imports and files removed

**🏗️ New Architecture Structure:**
```
campus_locker_system/
├── app/
│   ├── presentation/        # ✅ Web routes, templates, decorators
│   ├── services/           # ✅ Application orchestration layer
│   │   ├── parcel_service.py
│   │   ├── locker_service.py
│   │   ├── pin_service.py
│   │   ├── notification_service.py
│   │   ├── admin_auth_service.py
│   │   └── audit_service.py
│   ├── business/           # ✅ Pure domain logic (no dependencies)
│   │   ├── parcel.py
│   │   ├── locker.py
│   │   ├── pin.py
│   │   ├── notification.py
│   │   ├── admin_auth.py
│   │   └── audit.py
│   ├── adapters/           # ✅ External system interfaces
│   │   ├── email_adapter.py
│   │   ├── database_adapter.py
│   │   └── audit_adapter.py
│   └── persistence/        # ✅ Database models
├── tests/                  # ✅ Comprehensive test suite (91 tests)
├── .github/workflows/      # ✅ CI/CD pipeline
├── Makefile               # ✅ Development commands
├── pytest.ini            # ✅ Test configuration
├── requirements.txt       # ✅ Professional dependencies
└── BRANCHING_STRATEGY.md  # ✅ Safe git workflow
```

**🧹 Phase 5 Code Cleanup - COMPLETED:**
- ✅ **Legacy Import Cleanup**: Removed all legacy imports from `app.application.services`
- ✅ **Import Structure Cleaned**: Updated to modern hexagonal architecture imports
- ✅ **Service Call Standardization**: Consistent audit logging patterns
- ✅ **Business Domains Successfully Extracted**: 6 domains with clean separation
- ✅ **External System Adapters**: Email, Database, and Audit adapters implemented
- ✅ **Development Excellence**: Safe branching strategy and professional CI/CD pipeline

**🎯 Business Domains Successfully Extracted:**
1. **Parcel Management** 🚚: Parcel lifecycle, status transitions
2. **Locker Management** 🔒: Size validation, availability rules
3. **PIN Management** 🔐: PIN generation, validation, expiry
4. **Notification Management** 📧: Email templates, delivery rules
5. **Admin & Authentication** 👤: Auth rules, session policies
6. **Audit Logging** 📝: Event classification, retention policies

**🔌 External System Adapters:**
- **Email Adapter**: Clean email abstraction with Flask-Mail and Mock implementations
- **Database Adapter**: Repository pattern for data access with SQLAlchemy and In-memory implementations
- **Audit Adapter**: Audit log persistence abstraction with Database and Mock implementations

**⚡ Development Excellence:**
- ✅ **Safe Branching Strategy**: Never push to main, feature branches, pull requests
- ✅ **Professional CI/CD Pipeline**: Multi-Python testing, code quality checks, security scanning
- ✅ **100% Test Preservation**: Started and ended with 91 passing tests
- ✅ **Code Quality Improvements**: Legacy imports eliminated, dependency direction corrected
- ✅ **Architecture Validation**: Hexagonal principles fully implemented

---

#### BRANCHING_STRATEGY.md - Safe Development Workflow

**Safe Development Workflow 🛡️**

**Golden Rule: NEVER push directly to `main` branch!**

**Branch Structure:**
- **`main`** - Production-ready code only (protected)
- **`develop`** - Integration branch for testing features together
- **`feature/*`** - New features (e.g., `feature/new-dashboard`)
- **`bugfix/*`** - Bug fixes (e.g., `bugfix/fix-login-error`)
- **`hotfix/*`** - Emergency fixes (e.g., `hotfix/security-patch`)

**Typical Workflow:**
1. **Starting New Work**: Checkout develop, pull latest, create feature branch
2. **Working on Branch**: Make changes, commit, push to feature branch (not main!)
3. **Testing Changes**: Run tests locally before pushing
4. **Getting Code to Main**: Push branch, create Pull Request, CI runs, review, merge

**Benefits:**
- 🛡️ **Main branch is always stable**
- 🧪 **Test changes safely on branches**
- 👥 **Easy collaboration with team members**
- 🔄 **Clear history of what changed when**
- ⚡ **Fast to rollback if something goes wrong**

---

#### README_HEXAGONAL.md - Migration Plan Documentation

**Hexagonal Architecture Migration Plan**

**Migration Phases:**
1. **Skeleton**: Create new folders and README (this file). No code moved yet.
2. **Domain Extraction**: Move code into `business/`, `services/`, and update imports. Test after each move.
3. **Adapters**: Move external system logic (mail, etc.) to `adapters/`.
4. **Persistence**: Refine repository interfaces and adapters in `persistence/`.
5. **Testing**: Ensure all tests pass after each phase.

**✅ COMPLETED:**
- **Phase 1**: Repository skeleton with hexagonal folder structure
- **Phase 2**: Domain extraction (6/6 domains completed)
  - Parcel Management Domain ✅
  - Locker Management Domain ✅
  - PIN Management Domain ✅
  - Notification (Email) Management Domain ✅
  - Admin & Auth Management Domain ✅
  - Audit Logging Management Domain ✅
- **Phase 3**: Adapter implementation (3/3 adapters completed) ✅
  - Email Adapter (Flask-Mail abstraction) ✅
  - Database Adapter (SQLAlchemy abstraction) ✅
  - Audit Adapter (Audit logging abstraction) ✅
- **Phase 4**: CI & tests refinement ✅
- **Phase 5**: Code cleanup and legacy removal ✅

**Test Status**: 91/91 tests passing (100% success rate)
**Architecture**: Clean hexagonal architecture with external system abstractions

---

#### DOCKER_DEPLOYMENT.md - Containerization Guide

**🐳 Campus Locker System - Docker Deployment Guide**

**Architecture Overview:**
The Docker deployment includes:
- **🚀 Flask Application** (Gunicorn + Python 3.12)
- **🔄 Nginx Reverse Proxy** (Load balancing, SSL termination)
- **📧 MailHog** (Email testing service)
- **🗄️ SQLite Database** (Persistent storage)
- **⚡ Redis** (Caching and sessions)

**Quick Start:**
```bash
# Build and start services
make build
make up

# Test deployment
make test

# Access services
# Main Application: http://localhost
# MailHog Web UI: http://localhost:8025
# Health Check: http://localhost/health
```

**Service Details:**
- **Main Application Container**: Custom Python 3.12 slim, Gunicorn WSGI server, health checks
- **Nginx Reverse Proxy**: Load balancing, compression, security headers
- **MailHog Email Service**: Email testing and development
- **Redis Cache**: Session storage and caching with persistence

**Available Make Commands:**
```bash
make help          # Show all available commands
make build         # Build Docker images
make up            # Start production deployment
make down          # Stop production deployment
make logs          # View production logs
make test          # Test deployment
make clean         # Clean up Docker resources
make dev-up        # Start development deployment
make dev-down      # Stop development deployment
make dev-logs      # View development logs
```

**Security Features:**
- Non-root containers for all services
- Security headers via Nginx
- Health checks and monitoring
- Network isolation between services
- Volume permissions and ownership

**Production Considerations:**
- SSL/HTTPS setup with certificates
- Performance tuning and scaling
- Monitoring and logging
- Backup and recovery procedures

---

**Campus Locker System v2.0** - Secure, Scalable, Production-Ready 🚀