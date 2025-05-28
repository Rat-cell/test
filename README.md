# Campus Locker System v2.1.1 - Team I

## 🚀 Version 2.1.1 - Email Template Enhancement & System Standardization

**Campus Locker System** is now fully containerized and production-ready! Version 2.1.1 introduces professional email templates, enhanced PIN regeneration, and comprehensive system standardization.

### 🎯 What's New in v2.1.1

- **🎨 Professional Email Templates**: Completely redesigned email templates with clean, professional formatting
- **🔄 Enhanced PIN Regeneration**: All PIN-related emails now include regeneration links for improved user experience
- **📅 Parcel Lifecycle Clarity**: All emails include pickup deadline information (7 days from deposit)
- **🌐 URL Standardization**: Consistent localhost URL structure throughout the entire system
- **🗄️ Database Optimization**: Additional test lockers and improved data structure for comprehensive testing
- **🔧 Configuration Improvements**: Flask port migration to 80 and nginx upstream fixes

### ✨ Previous v2.1 Features
- **🔒 Enhanced Security**: PIN security - depositors can no longer see pickup PINs
- **📧 Fixed Email System**: Emails now properly route to MailHog for testing
- **🗄️ Auto Database Seeding**: 18 pre-configured lockers and admin user ready on startup
- **🔧 Environment Configuration**: All email settings now configurable via environment variables
- **🧪 Manual Testing Ready**: Complete workflow from deposit to pickup with email verification
- **📚 Updated Documentation**: Correct admin credentials and testing procedures

### ✨ Previous v2.0 Features
- **🐳 Full Docker Containerization**: Production and development environments
- **🔄 Nginx Reverse Proxy**: Load balancing, security headers, SSL-ready
- **📧 Integrated Email Testing**: MailHog for development and testing
- **⚡ Redis Caching**: Session storage and performance optimization
- **🏥 Health Monitoring**: Automated health checks and service dependencies
- **🔒 Security Hardened**: Non-root containers, security headers, proper secrets management
- **📊 Comprehensive Logging**: Structured logging with rotation and monitoring
- **🧪 Enhanced Testing**: Containerized test environment with 91 passing tests

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
- **🏠 Main Application**: http://localhost
- **💊 Health Check**: http://localhost/health
- **📧 Email Testing (MailHog)**: http://localhost:8025
- **🔧 Direct App Access**: http://localhost

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
│   Port 80/443   │    │    Port 80      │    │   Port 6379     │
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
- **Command**: `make up`
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
make up         # Start development deployment
make down       # Stop development deployment
make logs       # View development logs

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
- **Ports**: 5001 (external), 80 (internal)
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
make up

# View logs
make logs

# Run tests in container
docker-compose exec app pytest

# Stop development environment
make down
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
curl http://localhost/health
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
curl http://localhost/health   # Nginx proxy access (recommended)
curl http://localhost/health  # Direct app access (debugging only)
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

You should see output indicating the server is running, usually on http://localhost/.
Access the Application:

Open your web browser and go to http://localhost/deposit to deposit a parcel.
Go to http://localhost/pickup to pick up a parcel.
Go to http://localhost/admin/login to log in as an admin.

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

#### Version 2.1.1 (Current) - Email Template Enhancement & System Standardization
**Release Date**: January 2025

**🎨 Email Template Overhaul:**
- **Professional Email Design**: Completely redesigned all email templates with clean, professional formatting
- **Removed Clutter**: Eliminated excessive emojis and verbose text for better readability
- **Consistent Styling**: Standardized formatting across all email types with clear section headers
- **Dynamic Configuration**: All templates now use configurable PIN expiry and parcel lifecycle values

**🔄 PIN Regeneration Enhancement:**
- **Universal Regeneration Links**: All PIN-related emails now include "🔄 NEED A NEW PIN?" section
- **Always Available**: Recipients can regenerate PINs from any PIN-related email, not just the initial notification
- **Improved User Experience**: Clear instructions and accessible regeneration throughout the PIN lifecycle

**📅 Parcel Lifecycle Information:**
- **Pickup Deadline Clarity**: All emails now include "7 days from deposit" pickup deadline information
- **Dynamic Configuration**: Parcel pickup deadlines read from `PARCEL_MAX_PICKUP_DAYS` configuration
- **Security Notes**: Enhanced security information about timeframes and PIN validity

**🌐 URL Configuration Standardization:**
- **Consistent URL Structure**: Standardized all URL references throughout the codebase to use `localhost` (port 80)
- **Flask Port Migration**: Migrated Flask application from port 5000 to port 80 internally for consistency
- **Nginx Upstream Fix**: Updated nginx configuration to properly proxy to Flask on port 80
- **Documentation Updates**: Updated all documentation files with correct URLs

**🗄️ Database & Configuration Improvements:**
- **Locker Availability**: Added additional test lockers to ensure sufficient availability for all sizes
- **Database Cleanup**: Freed occupied lockers and added new lockers for comprehensive testing
- **Configuration Files**: Updated Flask, Docker Compose, and Nginx configurations for consistency

---

#### Version 2.0.0 - Docker Production Deployment
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
https://www.plantuml.com/plantuml/uml/SyfFKj2rKt3CoKnELR1Io4ZDoSa70000
---
####OLD VERSIONS


### Version 1.8.5 - Hexagonal Architecture Foundation

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



###Version 1.8.4 - Legacy Monolithic Application

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
###Version 1.81 (Changelog)
Log Management Improvements:
Standardized all application logs to the root-level logs/ folder. Why/How: Prevents confusion and ensures all logs are in one place by updating the logging config and cleaning up duplicates.
Documented log rotation policy (10 KB per file, 10 backups, oldest deleted on rotation). Why/How: Ensures logs don't grow indefinitely and are easy to manage; added clear documentation for maintainers.
Added best practices for log monitoring and configuration. Why/How: Helps future developers/admins understand how to monitor and tune logging for their needs.
Removed duplicate/legacy log folders and files. Why/How: Reduces clutter and risk of confusion or missed logs.
Clearly labeled that only main application logs are stored in logs/; audit logs are in the database. Why/How: Clarifies log purpose and storage for maintainers and auditors.
Testing and Structure:
Split and reorganized tests by user flow and edge cases for clarity and maintainability. Why/How: Makes it easier to find, run, and extend tests for specific flows or features.
Added a dedicated admin log flow test to ensure audit logging of admin actions. Why/How: Verifies that admin actions are properly recorded for security and traceability.
Confirmed all test files are connected and documented. Why/How: Ensures no orphaned or untested flows remain after restructuring.
Fixed all expired vs return_to_sender test issues: Why/How: Updated tests to expect the correct status (return_to_sender and awaiting_collection) for overdue parcels, matching the current application logic and ensuring all tests pass.
Documentation:
Updated the main README to include all log and test documentation in one place. Why/How: Centralizes project knowledge for easier onboarding and reference.
Removed the separate logs/README.md for simplicity and clarity. Why/How: Avoids duplication and ensures all documentation is up to date.
Added detailed explanations of log types, rotation, and best practices. Why/How: Helps maintainers understand and manage logs effectively.
Known Issues:
Some tests expect a parcel status of expired after overdue, but the system now uses return_to_sender. This is a known mismatch between code and test expectations.
---
###V.1.80b

Refactored tests for robustness and best practices:
Split admin/anonymous access tests for session isolation.
Used substring assertions for flashed messages and sensor data to avoid issues with HTML formatting/escaping.
Matched error codes and messages to actual Flask/API behavior.
Ensured all tests pass with the current codebase and configuration.
Improved test coverage and reliability for admin locker management, sensor data display, and error handling.
Updated test and code comments for clarity and maintainability.
Added MailHog Docker Compose configuration for local email testing.
Cleaned up impossible code paths and tests (e.g., deposited_at is None for parcels).
For a detailed commit history, see the project's git log.
---

### Appendix B: Original README (v1.81)
1. Project Overview
Purpose: This project is a browser-based campus locker system. It allows senders (like students or couriers) to deposit parcels and recipients to pick them up 24/7 using a one-time PIN.
Technology Stack: The core system is built with Python and the Flask web framework. It uses an SQLite database for storage and MailHog for local email testing (to simulate sending PINs).
Team: Developed by Team I (Pauline Feldhoﬀ, Paul von Franqué, Asma Mzee, Samuel Neo, Gublan Dag) as part of the Digital Literacy IV: Software Architecture course.
Note: This is an initial implementation focusing on core deposit and pickup functionalities. All locker hardware is simulated.
2. OLDDDDDDDDDD Getting Started: Setup & Running the Application
Follow these steps to get the application running on your local machine (macOS is the primary demo environment, but it should work on other systems with Python).

Prerequisites:
Python 3.7+: Ensure you have Python installed. You can check by opening a terminal and typing python --version or python3 --version.
pip: Python's package installer, usually comes with Python.
MailHog (for email testing):
MailHog is a tool that catches emails sent by the application locally, so you don't need a real email server for development.
The easiest way to run MailHog is using Docker:
docker run -d -p 1025:1025 -p 8025:8025 mailhog/mailhog
After running this, you can view received emails by opening your web browser and going to http://localhost:8025.
If you don't have Docker, you can download MailHog directly from its GitHub releases page.
OLDDDDDDDD Setup Steps:
Clone/Download the Code:

If you have git, clone the repository. Otherwise, download the source code files and place them in a directory, let's call it campus_locker_system.
Navigate to Project Directory:

Open your terminal and change to the project directory:
cd path/to/campus_locker_system
Create a Virtual Environment (Recommended):

It's good practice to keep project dependencies separate.
python3 -m venv venv
source venv/bin/activate
You should see (venv) at the beginning of your terminal prompt.
Install Dependencies:

Install all the required Python packages:
pip install -r requirements.txt
This will install Flask, SQLAlchemy (for the database), Bcrypt (for password hashing), Flask-Mail, and Pytest (for testing).
Database Setup:

The application uses SQLite databases. The app will create campus_locker.db and campus_locker_audit.db in the databases/ folder on first run.
The necessary tables within these databases will also be created automatically.
Create an Admin User:

To access admin functionalities (though limited in this version), you need an admin user.
Run the provided script from the campus_locker_system directory:
python create_admin.py your_admin_username your_admin_password
Replace your_admin_username and your_admin_password with your desired credentials. For example: python create_admin.py admin adminpass123.
Note: The admin password must be at least 8 characters long.
Run the Application:

Start the Flask development server:
python run.py
You should see output indicating the server is running, usually on http://localhost/.
Access the Application:

Open your web browser and go to http://localhost/deposit to deposit a parcel.
Go to http://localhost/pickup to pick up a parcel.
Go to http://localhost/admin/login to log in as an admin.
3. Project Structure Explained
The project code is organized into several main parts within the campus_locker_system directory:

app/: This is the heart of the Flask application.
__init__.py: Initializes the Flask application, database, mail system, and ties different parts together.
config.py: Contains configuration settings (like database location, mail server settings).
application/: Contains the "business logic" or "brains" of the system.
services.py: Functions that perform core tasks like assigning a locker, generating PINs, processing pickups, and verifying admin users.
persistence/: Manages data storage.
models.py: Defines the structure of the database tables (Lockers, Parcels, Admin Users, Audit Logs) using SQLAlchemy.
presentation/: Handles what the user sees and interacts with (the user interface).
routes.py: Defines the web page URLs (like /deposit, /pickup) and connects them to Python functions that decide what to do and what HTML to show.
templates/: Contains HTML files that structure the web pages.
admin/: HTML files specific to admin pages.
tests/: Contains automated tests written using Pytest to check if different parts of the application work correctly.
create_admin.py: The script mentioned earlier to create an admin user.
run.py: A simple script to start the Flask development server.
requirements.txt: Lists all the Python packages the project depends on.
**databases/: Contains all database files (campus_locker.db, campus_locker_audit.db).
logs/: Contains log files (e.g., campus_locker.log) that record application activity and errors. (This directory is created when the app runs).
4. Key Features Implemented
Parcel Deposit: Senders can specify parcel size and recipient email. The system assigns a locker and generates a unique 6-digit PIN.
PIN Display & Email: The PIN is shown on-screen to the sender and also emailed to the recipient (via MailHog for local viewing).
Parcel Pickup: Recipients use the 6-digit PIN to pick up their parcel. PINs expire after 24 hours.
Secure PIN Storage: PINs are not stored directly. Instead, a secure hash (salted SHA-256) of the PIN is stored, making it very difficult to reverse.
Admin Login: A basic login system for administrators. Admin passwords are also securely hashed (using bcrypt).
Audit Trail: Records key system events like parcel deposits, pickups (successful and failed attempts), admin logins/logouts, and email notification status. These logs are viewable by administrators.
Locker Status Management (Admin): Administrators can view all lockers and change their status (e.g., mark as 'out_of_service' or return to 'free' if empty). This helps manage faulty or reserved lockers.
Parcel Interaction Confirmation (Backend Logic): Supports backend logic for a locker client to allow senders to retract a mistaken deposit or recipients to dispute a pickup within a short window. This introduces new parcel statuses ('retracted_by_sender', 'pickup_disputed') and a locker status ('disputed_contents'). These new states currently require administrative follow-up for full resolution.
Report Missing Item (FR-06): Allows administrators to mark a parcel as 'missing'. Also provides an API endpoint for a locker client to signal a recipient reporting a parcel as missing immediately after a pickup attempt. This sets the parcel status to 'missing' and typically takes the associated locker out of service for investigation.
Automated Tests: Basic tests ensure core features are working as expected.
4.1. Viewing Audit Logs
Logged-in administrators can view a trail of system events to monitor activity. This includes records of:

Parcel deposits (initiated, successful, failed)
Parcel pickups (initiated, successful, failed due to invalid PIN or expiry)
Admin logins (successful, failed) and logouts
Email notification sending status
To view the audit logs, navigate to: /admin/audit-logs

The log displays the timestamp (UTC), the type of action, and a details field (in JSON format) providing more context about the event. The page shows the latest 100 entries.

4.2. Managing Locker Statuses (FR-08)
Administrators have the ability to manage the operational status of individual lockers. This is useful for handling maintenance, reservations, or other situations requiring a locker to be temporarily unavailable.

Access: Logged-in administrators can navigate to /admin/lockers to view a list of all lockers, their sizes, and their current operational statuses (e.g., 'free', 'occupied', 'out_of_service').
Actions Available:
Mark as 'Out of Service': Any locker can be marked as 'out_of_service'. If it was 'free', it will no longer be assigned for new parcel deposits. If it was 'occupied', it remains 'out_of_service' (and the parcel can still be picked up; the locker will then be 'out_of_service' and empty).
Mark as 'Free': A locker currently marked 'out_of_service' can be returned to 'free' status, making it available for new deposits. This action is only permitted if the locker does not contain an active ('deposited') parcel.
Auditing: All changes to locker statuses made by administrators are recorded in the audit log.
4.3. API Endpoints for Locker Client Interaction
The system now includes a set of API endpoints under the /api/v1/ prefix, intended for use by a separate locker hardware client system:

POST /api/v1/deposit/<parcel_id>/retract: Called by the locker client if a sender indicates they made a mistake immediately after depositing a parcel. This marks the parcel as 'retracted_by_sender' and frees the locker (if it was not 'out_of_service').
POST /api/v1/pickup/<parcel_id>/dispute: Called by the locker client if a recipient indicates an issue (e.g., wrong item, empty locker) immediately after a pickup attempt. This marks the parcel as 'pickup_disputed' and the locker as 'disputed_contents', requiring admin attention.
POST /api/v1/parcel/<int:parcel_id>/report-missing: Called by the locker client if a recipient, immediately after opening a locker with a valid PIN, reports that the parcel is not there or is incorrect. This sets the parcel status to 'missing' and may take the locker out of service.
These endpoints are designed for machine-to-machine communication and do not have a direct user interface in this web application. Authentication for these endpoints would be required in a production system.

4.4. Managing and Reporting Missing Parcels (FR-06)
Administrators can manage parcels that are reported or suspected to be missing. This complements the API endpoint that allows a locker client to report a missing parcel on behalf of a recipient.

Viewing Parcel Details: Admins can view detailed information for any parcel by navigating to /admin/parcel/<parcel_id>/view. This page can be accessed via links from the main /admin/lockers page if a parcel is associated with a locker.
Marking a Parcel as Missing: From the parcel detail page, if a parcel is in a state like 'deposited' or 'pickup_disputed', an admin can mark it as 'missing'.
This action changes the parcel's status to 'missing'.
If the parcel was 'deposited' in a locker, or its pickup was disputed, the associated locker will typically be set to 'out_of_service' to allow for inspection.
This administrative action is recorded in the audit log.
5. Architectural Choices (Why things are built this way)
Flask Framework: A lightweight and flexible Python web framework, good for building web applications quickly.
Layered Architecture: The code is divided into layers (Presentation, Application, Persistence). This helps keep things organized:
Presentation handles user interaction.
Application handles the main logic and tasks.
Persistence handles database interactions. This separation makes the code easier to understand, test, and modify.
SQLAlchemy ORM: Used for interacting with the SQLite database. It allows developers to work with database records as Python objects, simplifying database operations.
SQLite Database: A simple file-based database, easy to set up and use for local development and small applications.
MailHog: For testing email functionality locally without needing a real email server. This is very convenient for development.
Security: PINs and admin passwords are not stored as plain text. They are "hashed" using strong algorithms (SHA-256 for PINs, bcrypt for admin passwords) to protect them even if the database file is compromised.
6. How to Run Tests
Make sure you have activated your virtual environment (source venv/bin/activate).
Navigate to the project root directory (campus_locker_system).
Run pytest from the terminal:
python -m pytest
Or simply:
pytest
You should see output indicating the number of tests passed.
6.1. Test Overview
The tests/edge_cases/ directory contains edge case tests for the most critical user and API flows. Each test is commented for clarity:

test_retract_edge_cases.py
test_api_retract_deposit_parcel_not_found: API should return 404 or 400 when trying to retract a non-existent parcel.
test_api_retract_deposit_not_deposited: API should return 400 or 409 when trying to retract a parcel that is not in 'deposited' state (already picked up).
test_api_retract_deposit_locker_was_oos: Retracting a deposit when the locker is out_of_service should succeed, but locker remains out_of_service.
test_dispute_edge_cases.py
test_dispute_pickup_parcel_not_found: Disputing pickup for a non-existent parcel should return an error.
test_dispute_pickup_parcel_not_picked_up: Disputing pickup for a parcel that has not been picked up should return an error.
test_pickup_edge_cases.py
test_process_pickup_fails_for_retracted_parcel: Picking up a parcel that has already been retracted should fail with 'Invalid PIN'.
test_process_pickup_fails_for_disputed_parcel: Picking up a parcel that has been disputed should fail with 'Invalid PIN'.
test_missing_edge_cases.py
test_report_missing_by_recipient_fail_not_found: Reporting a missing parcel with a non-existent ID should return an error.
test_report_missing_by_recipient_fail_wrong_state: Reporting a missing parcel in the wrong state (picked_up or expired) should return an error.
test_sensor_edge_cases.py
test_sensor_data_missing_has_contents: Submitting sensor data with missing 'has_contents' field should return 400.
test_sensor_data_invalid_type: Submitting sensor data with non-boolean 'has_contents' should return 400.
test_sensor_data_nonexistent_locker: Submitting sensor data for a non-existent locker should return 404 or 400.
test_pin_reissue_edge_cases.py
test_old_pin_invalid_after_regeneration: After PIN regeneration, the old PIN should be invalid and only the new PIN works.
Edge Case Coverage vs. Requirements

The following edge case requirements are not yet directly covered by the current tests and should be considered for future test development:

Configurable system behaviors (e.g., changing pickup time limit, locker dimensions, notification preferences via config)
Direct locker status updates via API or sensor integration
Email/mobile confirmation before sending PINs/codes
PIN reissue logic (ensuring new PIN invalidates old, only within pickup window)
Return-to-sender process after pickup window expiry
Explicit test that new PIN expires old PINs
The current edge case tests focus on invalid state transitions and error handling for the main user and API flows.

See the comments in each test file for more details on the scenarios covered.

6.2 Application Logs
All application logs are stored in the root-level logs/ folder. This includes:

campus_locker.log and its rotated versions: Main application logs (info, warnings, errors) from the Flask app and its services.
Log rotation policy:
Each log file is capped at 10 KB (10,240 bytes).
Up to 10 backup log files are kept (campus_locker.log.1 through .10).
When the main log exceeds 10 KB, it is rotated and the oldest log is deleted.
Best practices:
Monitor log file sizes and adjust maxBytes and backupCount in the logging configuration as needed for your deployment (e.g., increase for production).
Regularly review logs for errors and warnings.
Only main application logs are stored here. Audit logs are stored in the database table audit_log and are not written to files.
7. OLDDDDDDPotential Next Steps & Future Improvements
This initial version covers the core requirements. Based on the original project charter, future enhancements could include:

Full Audit Trail (FR-07): Logging every deposit, pickup, and admin action (currently partially implemented).
Advanced Admin Functions:
Re-issuing PINs (FR-05).
Flagging lockers as "out_of_service" (FR-08 - basic version implemented).
Reporting missing items (FR-06).
Admin resolution workflows for new parcel/locker states (e.g., 'retracted_by_sender', 'pickup_disputed', 'disputed_contents').
Web-Push Notifications (FR-03): Real-time notifications in the browser, in addition to email.
Reminder Notifications (FR-04): Automatic reminders after 24 hours of occupancy.
Nightly Backups: Regular backups of the SQLite database.
Enhanced UI/UX: Improving the user interface and experience, including keyboard-only navigation.
More Comprehensive Testing: Adding more unit and end-to-end tests.
Dockerization: Packaging the entire application with Docker Compose for easy one-command deployment (docker-compose up).
