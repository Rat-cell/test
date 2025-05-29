# Campus Locker System v2.1.3 - Team I

## 🚀 Version 2.1.3 - Database Infrastructure & Project Organization Overhaul

**Campus Locker System** is now production-hardened with comprehensive testing and enhanced deployment infrastructure! Version 2.1.3 introduces major database improvements, complete project reorganization, and robust deployment validation.

### 🗄️ Database Infrastructure Overhaul
- **Complete Database Testing**: Tested complete initialization and seeding process with removed databases to simulate first deployment
- **Docker Volume Fix**: Fixed critical docker-compose.yml configuration from named volumes to bind mounts (`./campus_locker_system/databases:/app/databases`)
  - Database files now properly created in local filesystem for debugging and backup
  - Fixed database persistence issues where files only existed inside containers
- **JSON Seeding Enhancement**: Improved locker seeding from JSON configurations with comprehensive validation
- **Database Lifecycle Management**: Enhanced database creation, population, and reset processes

### 🐳 Docker Deployment Improvements  
- **Container Rebuild Testing**: Simulated complete first deployment scenarios with fresh container builds
- **Volume Configuration Fix**: Resolved database file visibility issues on host filesystem
- **Health Check Validation**: Enhanced container startup and health verification processes
- **Fresh Installation Testing**: Comprehensive testing of deployment from scratch scenarios

### 🧪 Comprehensive Testing Framework
- **Deployment Flow Testing**: Created complete deployment_flow.py test with 6 critical validation steps:
  1. Remove existing database files to simulate fresh deployment
  2. Rebuild Docker containers with no cache for clean state
  3. Start containers and verify fresh initialization process
  4. Verify database files are properly created in local filesystem
  5. Verify correct seeding with expected locker count (18 lockers)
  6. Verify safety protection mechanisms against re-seeding
- **Edge Case Testing Expansion**: Enhanced locker overwrite protection with comprehensive scenarios:
  - Duplicate ID conflict detection and prevention
  - Existing database conflict protection mechanisms
  - Invalid JSON data validation and rejection
  - Partial conflict scenarios and recovery procedures
  - Database recovery mechanisms from failed operations
- **Test Organization**: Properly organized test structure with clear separation of concerns

### 📁 Project Structure Reorganization
- **Test Directory Cleanup**: Consolidated and organized test structure
  - Moved deployment flow test to proper location (`campus_locker_system/tests/flow/`)
  - Consolidated all edge case tests in `campus_locker_system/tests/edge_cases/`
  - Removed duplicate test directories between root and campus_locker_system
- **Documentation Consolidation**: Major cleanup of duplicate documentation
  - Updated root directory with latest versions of DATABASE_DOCUMENTATION.md and INTEGRATION_SUMMARY.md
  - Removed outdated duplicates from campus_locker_system/ directory
  - Ensured single source of truth for all documentation
- **Configuration Management**: 
  - Merged configuration and safety guides into comprehensive LOCKER_OPERATIONS_GUIDE.md
  - Removed empty config/ directory after relocating contents
  - Updated all references to operational guides in documentation

### 🔍 Comprehensive Duplicate File Audit
- **Systematic Duplicate Detection**: Performed complete codebase scan using MD5 checksums to identify all duplicate files
- **File Deduplication**: Removed multiple sets of duplicate files:
  - Empty test flow placeholder files (test_pickup_flow.py, test_deposit_flow.py, test_api_flow.py, test_admin_flow.py)
  - Duplicate seeding scripts (removed campus_locker_system/scripts/seed_lockers.py, kept main version)
  - Empty and duplicate shell scripts (test-deployment.sh variants)
  - Misnamed test files that were actually old management scripts
- **Scripts Directory Organization**: 
  - Maintained proper separation: root scripts/ for infrastructure, campus_locker_system/scripts/ for utilities
  - Removed empty and duplicate script files
  - Preserved functional separation of concerns

### 🛠️ Development Workflow Improvements
- **Makefile Analysis**: Documented and validated that two Makefiles serve distinct purposes:
  - Root Makefile: Docker deployment operations (build, up, down, logs, test, clean)
  - campus_locker_system/Makefile: Development workflow (install, test, lint, format, security)
- **Command Structure Validation**: Verified no functional overlap between deployment and development commands
- **Build Process Enhancement**: Improved build and deployment testing procedures

### 🔧 Configuration and JSON Management
- **JSON Configuration Processing**: Enhanced handling of locker configuration JSON files
- **Seeding Process Improvement**: Improved database seeding with better validation and error handling
- **Configuration File Organization**: Streamlined configuration file structure and location
- **Environment Configuration**: Better separation of configuration concerns

### 📋 Database Documentation and Safety
- **Overwrite Protection**: Enhanced safety mechanisms for database operations
- **Seeding Safety**: Implemented comprehensive protection against accidental data loss
- **Database State Validation**: Added thorough validation of database states before operations
- **Recovery Procedures**: Documented and tested database recovery scenarios
- **Architecture Integration**: Key database architecture details integrated into README with reference to complete DATABASE_DOCUMENTATION.md
- **Operations Guide Consolidation**: Comprehensive LOCKER_OPERATIONS_GUIDE.md with step-by-step safety procedures, troubleshooting, and emergency recovery

### 🚀 Deployment Process Enhancement
- **First Deployment Simulation**: Comprehensive testing of complete deployment from scratch
- **Container Management**: Improved Docker container lifecycle management
- **Database Initialization**: Enhanced fresh database setup and seeding processes
- **Validation Workflows**: Added systematic validation of deployment success

### 🐛 Critical Fixes
- **Docker Volume Configuration**: Fixed fundamental issue with database file persistence
- **Test Structure**: Resolved test organization and duplicate issues
- **File Duplication**: Eliminated numerous duplicate files causing maintenance confusion
- **Documentation Consistency**: Fixed outdated and conflicting documentation

### ✨ Enhanced Monitoring and Validation
- **Health Check Integration**: Improved application health monitoring during deployment
- **Database State Monitoring**: Enhanced tracking of database file creation and population
- **Seeding Validation**: Added comprehensive validation of seeding operations
- **Container State Verification**: Improved verification of container health and functionality

### 📚 Documentation Updates
- **Integration Documentation**: Updated INTEGRATION_SUMMARY.md with corrected configuration references
- **Database Documentation**: Enhanced DATABASE_DOCUMENTATION.md with latest procedures
- **Configuration Guide**: Relocated and updated LOCKER_CONFIGURATION_GUIDE.md
- **Deployment Procedures**: Documented comprehensive deployment and testing workflows

### 🗑️ Major Cleanup Accomplished
- **Removed Directories**: config/ (empty after file relocation)
- **Removed Duplicate Files**: DATABASE_DOCUMENTATION.md, INTEGRATION_SUMMARY.md (campus_locker_system versions)
- **Removed Empty Files**: Multiple empty test files and placeholder scripts
- **Removed Misnamed Files**: test files that were actually old management scripts
- **Removed Duplicate Scripts**: seed_lockers.py and test-deployment.sh duplicates

### 📋 Files Created/Enhanced
- `campus_locker_system/tests/flow/deployment_flow.py` - Comprehensive deployment testing
- `campus_locker_system/tests/edge_cases/test_locker_overwrite_protection_edge_cases.py` - Enhanced edge case testing
- `LOCKER_OPERATIONS_GUIDE.md` - Comprehensive operational guide (merged from configuration + safety guides)

### 🔄 Files Modified
- `docker-compose.yml` - Critical volume configuration fix for database persistence
- `DATABASE_DOCUMENTATION.md` - Updated with latest procedures and information
- `INTEGRATION_SUMMARY.md` - Updated configuration references and latest practices
- Multiple test files - Enhanced organization and functionality

---

### ✨ Previous v2.1.1 Features
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
- **Database**: SQLite with audit logging and persistent storage
- **Frontend**: HTML templates with responsive design
- **Containerization**: Docker, Docker Compose with optimized volume configuration
- **Reverse Proxy**: Nginx with security headers
- **Caching**: Redis for sessions and performance
- **Email Testing**: MailHog for development
- **Testing**: Pytest with 91 comprehensive tests + deployment flow validation
- **Configuration**: Safety-first architecture with persistent JSON configuration

### Team
Developed by **Team I**: Pauline Feldhoff, Paul von Franqué, Asma Mzee, Samuel Neo, Gublan Dag as part of the Digital Literacy IV: Software Architecture course.

### 🛡️ Safety-First Architecture

The system implements **safety-first principles** with automatic backups, conflict detection, and multi-mode operations to prevent data loss in production environments.

#### **Safety Resources**
- **📖 [LOCKER_OPERATIONS_GUIDE.md](LOCKER_OPERATIONS_GUIDE.md)**: Comprehensive guide for safe configuration, operational procedures, troubleshooting, and emergency recovery

#### **Current Production Setup**
- **15 HWR lockers** (5 small, 5 medium, 5 large) configured and ready for production use
- **Persistent configuration** stored in `databases/lockers-hwr.json` with automatic backup protection

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

All important data is stored with proper persistence across container restarts:

- **`./campus_locker_system/databases`**: SQLite database files (bind mount)
  - `campus_locker.db` - Main business database with 15 HWR lockers
  - `campus_locker_audit.db` - Audit trail database
  - `lockers-hwr.json` - Persistent locker configuration
  - `campus_locker_backup_*.db` - Automatic safety backups
- **`app_logs`**: Application log files
- **`redis_data`**: Redis cache and session data
- **`app_data`**: Additional application data

#### **Persistent Configuration Architecture**
The system uses a **configuration separation strategy**:
- **Application Code** (`app/config.py`): Python configuration structure (version controlled)
- **User Data** (`databases/lockers-hwr.json`): Actual locker definitions (persistent storage)
- **Safety**: All configuration changes create automatic backups before execution

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

### Database Architecture

#### **Dual-Database Design**
The system uses a **separation of concerns** approach with two dedicated SQLite databases:

- **📊 Main Database** (`campus_locker.db`) - Core business operations and data
- **📋 Audit Database** (`campus_locker_audit.db`) - Administrative audit trail and security logs

Both databases are stored in the persistent `databases/` directory with automatic backup protection.

#### **Database Files Structure**
```
databases/
├── campus_locker.db              # Main business database
├── campus_locker_audit.db        # Audit trail database  
├── lockers-hwr.json              # Locker configuration (15 HWR lockers)
└── campus_locker_backup_*.db     # Automatic safety backups
```

#### **Main Database Schema** (`campus_locker.db`)

**Entity Relationship Diagram (ERD):**
```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│     LOCKER      │    │     PARCEL      │    │   ADMIN_USER    │
├─────────────────┤    ├─────────────────┤    ├─────────────────┤
│ id (PK)         │◄──┐│ id (PK)         │    │ id (PK)         │
│ location        │   ││ locker_id (FK)  │    │ username        │
│ size            │   ││ pin_hash        │    │ password_hash   │
│ status          │   ││ otp_expiry      │    │ last_login      │
└─────────────────┘   ││ recipient_email │    └─────────────────┘
                      ││ status          │
┌─────────────────┐   ││ deposited_at    │
│ LOCKER_SENSOR   │   ││ picked_up_at    │
│     _DATA       │   ││ pin_generation_*│
├─────────────────┤   │└─────────────────┘
│ id (PK)         │   │
│ locker_id (FK)  │◄──┘
│ timestamp       │
│ has_contents    │
└─────────────────┘
```

**Core Tables:**
- **`locker`**: Physical locker definitions with location, size (small/medium/large), and status
- **`parcel`**: Parcel lifecycle tracking with PIN security, recipient details, and timestamps
- **`admin_user`**: Administrator account management with secure password hashing
- **`locker_sensor_data`**: IoT sensor data collection for hardware integration

**Key Relationships:**
```
LOCKER (15 HWR lockers)
├── id, location, size, status
├── → PARCEL (1:many) - parcels stored in lockers
└── → LOCKER_SENSOR_DATA (1:many) - sensor readings

PARCEL
├── locker_id (FK), recipient_email, status
├── pin_hash, otp_expiry, deposited_at, picked_up_at
└── PIN regeneration fields (token, expiry, count)

ADMIN_USER
└── username, password_hash, last_login
```

#### **Audit Database Schema** (`campus_locker_audit.db`)

**Audit ERD:**
```
┌─────────────────┐
│   AUDIT_LOG     │
├─────────────────┤
│ id (PK)         │
│ timestamp       │
│ action          │
│ details         │
│ admin_id (FK)   │──────────► References admin_user.id 
│ admin_username  │            in main database
└─────────────────┘
```

**Audit Trail:**
- **`audit_log`**: Complete activity logging with timestamps, actions, admin tracking, and detailed event information

#### **Data Flow Overview**

**Business Operations:**
```
1. LOCKER (configured from JSON) 
   ↓
2. PARCEL (deposited into locker)
   ↓  
3. SENSOR_DATA (monitors locker contents)
   ↓
4. PARCEL (picked up, status updated)
```

**Administrative Operations:**
```
1. ADMIN_USER (authenticates)
   ↓
2. AUDIT_LOG (action recorded)
   ↓
3. Business Operations (lockers, parcels)
   ↓
4. AUDIT_LOG (results recorded)
```

#### **Production Data Overview**
- **15 HWR lockers** configured from `databases/lockers-hwr.json`
- **Equal distribution**: 5 small, 5 medium, 5 large lockers
- **Simple naming**: "HWR Locker 1" through "HWR Locker 15"
- **Safety features**: Automatic backups, conflict detection, audit trail

#### **Database Resources**
For detailed database documentation including complete schemas, performance optimization, maintenance procedures, and monitoring queries, see:

**📖 [DATABASE_DOCUMENTATION.md](DATABASE_DOCUMENTATION.md)** - Complete database guide

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

## 🚀 Production Operations

### **Quick Deployment**
```bash
# Deploy and verify system health
make up
make test
```

### **Operational Procedures**
For detailed operational procedures including safe configuration management, adding lockers, troubleshooting, and emergency recovery, see:

**📖 [LOCKER_OPERATIONS_GUIDE.md](LOCKER_OPERATIONS_GUIDE.md)** - Complete operational guide

### **Production Readiness Checklist**

#### ✅ **System Status**
- [x] 15 HWR lockers configured and ready for production use
- [x] Safety-first operational procedures with automatic backups
- [x] Comprehensive testing and monitoring capabilities

#### ✅ **Infrastructure**
- [x] Docker containerization with persistent storage
- [x] Dual-database architecture (main + audit)
- [x] Health monitoring and automated recovery

---

## ⚙️ Configuration

### **Essential Environment Variables**
```bash
# Production settings
export FLASK_ENV=production
export SECRET_KEY=your-generated-secret-key
export PARCEL_MAX_PICKUP_DAYS=7
export MAIL_SERVER=mailhog
export MAIL_PORT=1025
```

### **Docker Compose Override**
For custom environment variables, create `docker-compose.override.yml`:
```yaml
version: '3.8'
services:
  app:
    environment:
      - SECRET_KEY=your-custom-secret
      - PARCEL_MAX_PICKUP_DAYS=14
```

### **Detailed Configuration**
For comprehensive configuration options including locker setup, JSON configuration files, environment variables, and advanced settings, see:

**📖 [LOCKER_OPERATIONS_GUIDE.md](LOCKER_OPERATIONS_GUIDE.md)** - Complete configuration guide

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